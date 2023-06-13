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

    def send(self, query, attempts=1):
        auth_response = requests.post(
            self._url,
            headers=self._headers,
            data=query,
        )

        if auth_response.status_code != 200:
            if attempts >= 3:
                raise Exception(f"Error fetching data: {auth_response.text}")
            return self.send(query, attempts=attempts + 1)

        response = auth_response.json()

        if response.get("errors"):
            raise Exception(response.get("errors"))

        return response["data"]["analytics"]["richStats"]["stats"]
