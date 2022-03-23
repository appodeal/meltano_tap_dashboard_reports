"""DashboardReports tap class."""


from typing import List
from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_dashboard_reports.streams import ReportStream


class TapDashboardReports(Tap):
    """DashboardReports tap class."""

    name = "tap-dashboard-reports"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            # required=True,
            description="The token to authenticate against the API service",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync",
        ),
        th.Property(
            "api_url",
            th.StringType,
            # required=True,
            default="https://api.mysample.com",
            description="The url for the API service",
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [
            ReportStream(tap=self, report=report)
            for report in self.config.get("reports")
        ]


cli = TapDashboardReports.cli
