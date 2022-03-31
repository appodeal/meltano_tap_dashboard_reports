import os
import json
import requests
from jinja2 import Environment
from datetime import date
from singer_sdk import typing as th
from singer_sdk import Stream


class ReportStream(Stream):
    def __init__(self, tap=None, report=None):
        self._report = report
        self._query_template = self._load_query_template()
        self._query_params = self._fetch_query_params()

        self._dimensions = list(
            map(lambda v: v["dimension"].lower(), self._query_params["variables"]["groupBy"])
        )
        self._measures = list(
            map(lambda v: v["id"].lower(), self._query_params["variables"]["measures"])
        )
        super().__init__(tap=tap)

    @property
    def name(self):
        """Return primary key dynamically based on user inputs."""
        return self._report["stream"]

    @property
    def primary_keys(self):
        """Return primary key dynamically based on user inputs."""
        return self._report.get("key_properties") or self._dimensions

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
            for field in (self._dimensions + self._measures)
        ]

        # Return the list as a JSON Schema dictionary object
        return th.PropertiesList(*properties).to_dict()

    def get_records(self, context):
        columns = self._dimensions + self._measures
        data = self._send_request()

        for row in data["analytics"]["richStats"]["stats"]:
            values = list(map(lambda x: x["value"], row))
            record = dict(zip(iter(columns), iter(values)))
            yield record

    def _load_query_template(self):
        with open(self._report["query"]) as f:
            return f.read()

    def _fetch_query_params(self):
        return json.loads(self._query_template)

    def _send_request(self):
        token = self.config.get('auth_token') or os.environ.get('TAP_DASHBOARD_REPORTS_AUTH_TOKEN')
        url = self.config.get('api_url') or os.environ.get('TAP_DASHBOARD_REPORTS_API_URL')

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json",
            "Accept": "text/plain",
        }

        query_template = Environment().from_string(self._query_template)
        query = query_template.render(
            start_date=self.config.get("start_date"),
            end_date=date.today().strftime("%Y-%m-%d"),
        )

        auth_response = requests.post(
            url,
            headers=headers,
            data=query,
        )

        response = auth_response.json()
        return response["data"]
