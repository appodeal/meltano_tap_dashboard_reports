"""DashboardReports tap class."""

import os
from typing import List
from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_dashboard_reports.streams import ReportStream

CONFIG_VARS = {
    "api_url": "TAP_DASHBOARD_REPORTS_API_URL",
    "auth_token": "TAP_DASHBOARD_REPORTS_AUTH_TOKEN",
    "default_start_date": "TAP_DASHBOARD_REPORTS_DEFAULT_START_DATE",
    "start_date": "TAP_DASHBOARD_REPORTS_START_DATE",
    "end_date": "TAP_DASHBOARD_REPORTS_END_DATE",
    "select": "TAP_DASHBOARD_REPORTS__SELECT_FILTER",
}


class TapDashboardReports(Tap):
    """DashboardReports tap class."""

    name = "tap-dashboard-reports"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "default_start_date",
            th.StringType,
            description="The earliest record date to sync",
        ),
        th.Property(
            "api_url",
            th.StringType,
            default="https://api.mysample.com",
            description="The url for the API service",
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""

        for k, v in CONFIG_VARS.items():
            if os.environ.get(v):
                self._config[k] = os.environ.get(v)

        return [ReportStream(tap=self, report=report) for report in self._reports()]

    def _reports(self):
        select = self.config.get("select")
        all_reports = self.config.get("reports")

        if select == "[]" or select == '[""]':
            return all_reports

        return list(
            filter(
                lambda r: (r["stream"] in select),
                all_reports,
            )
        )


cli = TapDashboardReports.cli
