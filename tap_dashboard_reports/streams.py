import json
from concurrent.futures import ThreadPoolExecutor

from singer_sdk import typing as th
from singer_sdk import Stream
from tap_dashboard_reports.query import render_query
from tap_dashboard_reports.client import Client
from tap_dashboard_reports.period import get_iterator


class ReportStream(Stream):
    def __init__(self, tap=None, report=None):
        self._report = report
        self._query_template = self._load_query_template()
        self._query_params = self._fetch_query_params()
        self._custom_key = self._report.get("key_property", None)
        self._take_ids = self._report.get("take_ids", [])
        self._columns = []

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
        """Return primary key dynamically based on user inputs.
        If in config doesn't have key key_property then take _dimensions
        If config has take_ids then we should create primary key for fields + _id postfix
        which are intersection of _dimensions and take_ids
        """
        # get fields which are in take_ids and in dimensions and add _id postfix
        ids_fields = frozenset(self._dimensions).intersection(self._take_ids)
        ids_fields = list(map(lambda x: f"{x}_id", ids_fields))

        primary_keys = [*self._dimensions, *ids_fields]
        if self._custom_key is not None:
            primary_keys.append(self._custom_key)

        return primary_keys

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
        properties = []
        columns = []

        # if field in take_ids - this is meant that this column should be integer
        # and from response we will take id value
        for field in (self._dimensions + self._measures):
            if field in self._take_ids:
                field_name = f"{field}_id"
                columns.append(field_name)
                properties.append(th.Property(field_name, th.IntegerType))
            columns.append(field)
            properties.append(th.Property(field, th.StringType))

        if self._custom_key is not None:
            properties.append(th.Property(self._custom_key, th.StringType))
            columns.append(self._custom_key)

        self._columns = columns
        # Return the list as a JSON Schema dictionary object
        return th.PropertiesList(*properties).to_dict()

    def get_records(self, context):
        data = self._fetch_all_reports()

        # indexes of columns that should be taken from id
        ids_indexes = [self._columns.index(f"{x}_id") for x in self._take_ids]

        for row in data:
            values = []
            for cell_index, cell in enumerate(row):
                if cell_index in ids_indexes:
                    values.append(cell.get("id"))
                values.append(cell.get("value") or cell.get("name"))
            record = dict(zip(iter(self._columns), iter(values)))
            yield record

    def _load_query_template(self):
        with open(self._report["query"]) as f:
            return f.read()

    def _fetch_query_params(self):
        query = render_query(self._query_template, **self._report.get("vars", {}))
        return json.loads(query)

    def _fetch_all_reports(self):
        client = Client(self.config)
        with ThreadPoolExecutor(max_workers=10) as executor:
            tasks = []
            for start_date, end_date in get_iterator(
                self.config, self._report
            ).iterate():
                tasks.append(
                    executor.submit(
                        self._fetch_one_report, client, start_date, end_date
                    )
                )

            data = []
            for t in tasks:
                data += t.result()
        return data

    def _fetch_one_report(self, client, start_date, end_date):
        query = render_query(
            self._query_template,
            start_date=start_date,
            end_date=end_date,
            **self._report.get("vars", {}),
        )
        result = client.send(query)
        if self._custom_key is not None:
            for data in result:
                pk = {
                    "id": None,
                    "__typename": self._custom_key,
                    "value": end_date.strftime("%Y-%m-%d"),
                }
                data.append(pk)
        return result


def _prepare_field_name(param):
    name = param["id"].lower()
    if param["day"] is not None:
        name = f'{name}_{param["day"]}'
    return name
