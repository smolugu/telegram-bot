import requests

from datetime import datetime


class ProjectXREST:

    _BASE_URL = "https://api.topstepx.com/api"

    def __init__(
        self,
        username: str,
        api_key: str,
    ):
        self._username = username
        self._api_key = api_key

        self._session = requests.Session()

        self._login()

    def _login(self):
        response = self._session.post(
            f"{self._BASE_URL}/Auth/loginKey",
            json={
                "userName": self._username,
                "apiKey": self._api_key,
            },
        )
        

        response.raise_for_status()

        data = response.json()
        print("Login response:", data)

        self._session.headers.update({
            "Authorization": f"Bearer {data['token']}",
            "Content-Type": "application/json",
        })

        print("ProjectX authentication successful")

    def retrieve_bars(
        self,
        contract_id: str,
        start: datetime,
        end: datetime,
    ):
        print("contract_id: ", contract_id)
        response = self._session.post(
            f"{self._BASE_URL}/History/retrieveBars",
            json={
                "contractId": contract_id,
                "live": False,
                "startTime": start.isoformat(),
                "endTime": end.isoformat(),
                "unit": 2,
                "unitNumber": 1,
                "limit": 20000,
                "includePartialBar": False,
            },
        )

        response.raise_for_status()

        data = response.json()

        # print("ProjectX retrieveBars response:")
        # print(data)

        return data

    def search_contracts(
        self,
        search_text: str,
        live: bool = False,
    ):
        response = self._session.post(
            f"{self._BASE_URL}/Contract/search",
            json={
                "searchText": search_text,
                "live": live,
            },
        )

        response.raise_for_status()

        data = response.json()

        print("ProjectX contract search response:")
        print(data)

        return data