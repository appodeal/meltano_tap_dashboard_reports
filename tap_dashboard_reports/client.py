import os
import requests


class Client:
    def __init__(self, config):
        token = config.get("auth_token")
        self._url = config.get("api_url")

        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-type": "application/json",
            "Accept": "text/plain",
        }

    def send(self, query):
        # date_from = os.environ.get("TAP_DASHBOARD_REPORTS_DATE_FROM")
        # date_to = os.environ.get("TAP_DASHBOARD_REPORTS_DATE_TO")
        # print(f"Date: {date_from} - {date_to} ------------------------------------------")

        # query = render_query(
        #     self._query_template,
        #     start_date=self.config.get("start_date"),
        #     end_date=datetime.now(),
        # )

        # return []

        auth_response = requests.post(
            self._url,
            headers=self._headers,
            data=query,
        )

        response = auth_response.json()
        return response["data"]["analytics"]["richStats"]["stats"]
