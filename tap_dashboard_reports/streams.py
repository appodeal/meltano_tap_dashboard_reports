import os
import json
import requests
from datetime import date
from singer_sdk import typing as th
from singer_sdk import Stream


class ReportStream(Stream):
    def __init__(self, tap=None, report=None):
        self.report = report
        self.query = self._load_query()

        self.dimensions = list(
            map(lambda v: v["dimension"].lower(), self.query["variables"]["groupBy"])
        )
        self.measures = list(
            map(lambda v: v["id"].lower(), self.query["variables"]["measures"])
        )
        super().__init__(tap=tap)

    @property
    def name(self):
        """Return primary key dynamically based on user inputs."""
        return self.report["stream"]

    @property
    def primary_keys(self):
        """Return primary key dynamically based on user inputs."""
        return self.report.get("key_properties") or self.dimensions

    # @property
    # def replication_key(self):
    #     """Return replication key dynamically based on user inputs."""
    #     result = self.config.get("replication_key")
    #     if not result:
    #         self.logger.warning("Danger: could not find replication key!")
    #     return result

    @property
    def schema(self) -> dict:
        """Dynamically detect the json schema for the stream.
        This is evaluated prior to any records being retrieved.
        """

        properties = [
            th.Property(field, th.StringType)
            for field in (self.dimensions + self.measures)
        ]

        # Return the list as a JSON Schema dictionary object
        return th.PropertiesList(*properties).to_dict()

    def get_records(self, context):
        columns = self.dimensions + self.measures
        data = self._send_request()

        for row in data["analytics"]["richStats"]["stats"]:
            values = list(map(lambda x: x["value"], row))
            record = dict(zip(iter(columns), iter(values)))
            yield record

    def _load_query(self):
        with open(self.report["query"]) as f:
            return json.load(f)

    def _send_request(self):
        token = self.config.get('auth_token') or os.environ.get('TAP_DASHBOARD_REPORTS_AUTH_TOKEN')
        url = self.config.get('api_url') or os.environ.get('TAP_DASHBOARD_REPORTS_API_URL')

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json",
            "Accept": "text/plain",
        }

        if self.config.get("start_date"):
            self.query["variables"]["dateFilters"][0]["from"] = self.config.get(
                "start_date"
            )

        self.query["variables"]["dateFilters"][0]["to"] = date.today().strftime(
            "%Y-%m-%d"
        )

        auth_response = requests.post(
            url, headers=headers, data=json.dumps(self.query)
        )

        response = auth_response.json()
        return response["data"]
