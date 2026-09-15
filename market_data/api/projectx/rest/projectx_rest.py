import time
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
        self._token = None

        self._login()

    @property
    def token(self) -> str:
        if not self._token:
            raise RuntimeError("ProjectX authentication token unavailable")
        return self._token
    
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
        if not data.get("success") or not data.get("token"):
            raise RuntimeError(
                f"ProjectX login failed: "
                f"{data.get('errorCode')} "
                f"{data.get('errorMessage')}"
            )
        print("Login response:", data)
        self._token = data["token"]

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
        print("contract_id:", contract_id)

        url = f"{self._BASE_URL}/History/retrieveBars"

        payload = {
            "contractId": contract_id,
            "live": False,
            "startTime": start.isoformat(),
            "endTime": end.isoformat(),
            "unit": 2,
            "unitNumber": 1,
            "limit": 20000,
            "includePartialBar": False,
        }

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                response = self._session.post(
                    url,
                    json=payload,
                    timeout=15,
                )

                # ProjectX rate limit
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")

                    if retry_after is not None:
                        wait_seconds = int(retry_after)
                    else:
                        wait_seconds = 30

                    print(
                        f"ProjectX rate limit reached (429). "
                        f"Waiting {wait_seconds} seconds "
                        f"(attempt {attempt}/{max_attempts})..."
                    )

                    if attempt == max_attempts:
                        response.raise_for_status()

                    time.sleep(wait_seconds)
                    continue

                response.raise_for_status()

                return response.json()

            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as e:

                print(
                    f"ProjectX retrieveBars failed "
                    f"(attempt {attempt}/{max_attempts}): {e}"
                )

                if attempt == max_attempts:
                    raise

                time.sleep(attempt)

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