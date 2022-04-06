import json

from singer_sdk import typing as th
from singer_sdk import Stream
from tap_dashboard_reports.query import render_query
from tap_dashboard_reports.client import Client
from tap_dashboard_reports.period import get_iterator
from datetime import date
from datetime import datetime
from dateutil.parser import parse
from dateutil import rrule
from dateutil.relativedelta import relativedelta


class ReportStream(Stream):
    def __init__(self, tap=None, report=None):
        self._report = report
        self._query_template = self._load_query_template()
        self._query_params = self._fetch_query_params()

        self._dimensions = list(
            map(
                lambda v: v["dimension"].lower(),
                self._query_params["variables"]["groupBy"],
            )
        )
        self._measures = list(
            map(lambda v: v["id"].lower(), self._query_params["variables"]["measures"])
        )
        super().__init__(tap=tap)

    @property
    def name(self):
        """Return primary key dynamically based on user inputs."""
        return self._report.get("stream")

    @property
    def primary_keys(self):
        """Return primary key dynamically based on user inputs."""
        return self._report.get(
            "key_properties", self._dimensions
        )  # or self._dimensions

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
        data = self._fetch_date()

        for row in data:
            values = list(map(lambda x: x["value"], row))
            record = dict(zip(iter(columns), iter(values)))
            yield record

    def _load_query_template(self):
        with open(self._report["query"]) as f:
            return f.read()

    def _fetch_query_params(self):
        return json.loads(self._query_template)

    def _fetch_date(self):
        c = Client(self.config)
        data = []

        for start_date, end_date in get_iterator(self.config, self._report).iterate():
            query = render_query(
                self._query_template,
                start_date=start_date,
                end_date=end_date,
            )

            data += c.send(query)

        return data
