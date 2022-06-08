import json
from concurrent.futures import ThreadPoolExecutor

from singer_sdk import typing as th
from singer_sdk import Stream
from tap_dashboard_reports.query import render_query, _format_date
from tap_dashboard_reports.client import Client
from tap_dashboard_reports.period import get_iterator

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
            map(_prepare_field_name, self._query_params["variables"]["measures"])
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
        if len(self.primary_keys) == 0:
            properties = [
            th.Property(field, th.StringType)
            for field in (self._dimensions + self._measures)
        ]
        else:   
            properties = [
                th.Property(field, th.StringType)
                for field in (self._dimensions + self._measures + [self.primary_keys])
            ]

        # Return the list as a JSON Schema dictionary object
        return th.PropertiesList(*properties).to_dict()

    def get_records(self, context):
        columns = self._dimensions + self._measures 
        data, start_date, end_date = self._fetch_all_reports()
        for row in data:
            values = list(map(lambda x: x.get("value") or x.get("name"), row))
            record = dict(zip(iter(columns), iter(values)))
        result = record
        if len(self.primary_keys) != 0:
            result[self.primary_keys] = _format_date(end_date)
        yield  result       

    def _load_query_template(self):
        with open(self._report["query"]) as f:
            return f.read()

    def _fetch_query_params(self):
        query = render_query(
            self._query_template,
            **self._report.get("vars", {})
        )
        return json.loads(query)

    def _fetch_all_reports(self):
        client = Client(self.config)
        with ThreadPoolExecutor(max_workers=10) as executor:
            tasks = []
            for start_date, end_date in get_iterator(self.config, self._report).iterate():
                tasks.append(executor.submit(self._fetch_one_report, client, start_date, end_date))

            data = []
            for t in tasks:
                data += t.result()
        return data, start_date, end_date

    def _fetch_one_report(self, client, start_date, end_date):
        query = render_query(
            self._query_template,
            start_date=start_date,
            end_date=end_date,
            **self._report.get("vars", {})
        )
        return client.send(query)


def _prepare_field_name(param):
    name = param["id"].lower()
    if param["day"] is not None:
        name = f'{name}_{param["day"]}'
    return name
