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
        auth_response = requests.post(
            self._url,
            headers=self._headers,
            data=query,
        )

        response = auth_response.json()

        if response.get("errors"):
            raise Exception(response.get("errors"))

        return response["data"]["analytics"]["richStats"]["stats"]
