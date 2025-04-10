import json
import logging
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
        self._schema = self._report.get("schema", {})
        # explode is a dictionary of dimension name and list of fields to explode
        self._explode = self._report.get("explode", {})
        # skip_primary_keys is a list of fields to skip from primary keys
        self._skip_primary_keys = self._report.get("skip_primary_keys", [])
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
    def dimensions_with_ids(self):
        dimensions = []
        for dimension in self._query_params["variables"]["groupBy"]:
            dimension = dimension["dimension"].lower()
            if dimension in self._take_ids:
                dimensions.append(f"{dimension}_id")
            if dimension in self._explode:
                for explode_field in self._explode[dimension]:
                    dimensions.append(f"{dimension}_{explode_field}")
                continue
            dimensions.append(dimension)
        return dimensions

    @property
    def fields_with_ids(self):
        fields = [*self.dimensions_with_ids, *self._measures]
        if self._custom_key is not None:
            fields.append(self._custom_key)
        return fields

    @property
    def fields(self):
        fields = [*self._dimensions, *self._measures]
        if self._custom_key is not None:
            fields.append(self._custom_key)
        return fields

    @property
    def primary_keys(self):
        """Return primary key dynamically based on user inputs.
        If in config doesn't have key key_property then take _dimensions
        """

        if self._custom_key is not None:
            p_keys = [*self.dimensions_with_ids, self._custom_key]
        else:
            p_keys = self.dimensions_with_ids

        return [key for key in p_keys if key not in self._skip_primary_keys]

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
            for field in self.fields_with_ids
            if field not in self._schema
        ]

        properties += [
            th.Property(field, th.DateTimeType) for field, type in self._schema.items()
        ]

        # Return the list as a JSON Schema dictionary object
        return th.PropertiesList(*properties).to_dict()

    def get_records(self, context):
        data = self._fetch_all_reports()

        # indexes of columns that should be taken from id
        ids_indexes = [self.fields.index(x) for x in self._take_ids]

        # explode_indexes = [self.fields.index(x) for x in self._explode.keys()]
        explode_indexes_map = {
            self.fields.index(x): self._explode[x] for x in self._explode.keys()
        }

        for row in data:
            values = []
            for cell_index, cell in enumerate(row):
                if cell_index in explode_indexes_map:
                    for explode_field in explode_indexes_map[cell_index]:
                        values.append(cell.get(explode_field))
                    continue
                if cell_index in ids_indexes:
                    values.append(cell.get("id"))
                values.append(cell.get("value") or cell.get("name"))
            record = dict(zip(iter(self.fields_with_ids), iter(values)))
            yield record

    def _load_query_template(self):
        with open(self._report["query"]) as f:
            return f.read()

    def _fetch_query_params(self):
        query = render_query(self._query_template, **self._report.get("vars", {}))
        return json.loads(query)

    def _fetch_all_reports(self):
        client = Client(self.config)
        with ThreadPoolExecutor(max_workers=5) as executor:
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
