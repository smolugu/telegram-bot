from datetime import date, datetime, timezone

from massive import RESTClient

class MassiveREST:

    _RESOLUTION = "1min"

    def __init__(self, api_key: str):
        self._client = RESTClient(api_key)

    @staticmethod
    def _to_unix_ns(dt: datetime) -> int:
        return int(dt.timestamp() * 1_000_000_000)

    @staticmethod
    def _to_date_str(value: date | None) -> str | None:
        return date.isoformat(value) if value else None

    def list_futures_aggregates(
        self,
        contract: str,
        start: datetime,
        end: datetime,
    ):  
        print("calling rest api list_futures_aggregates")
        # print(start)
        # print(type(start))

        # print(end)
        # print(type(end))

        # print(start.isoformat())
        # print(end.isoformat())
        return list(
            self._client.list_futures_aggregates(
                ticker=contract,
                resolution=self._RESOLUTION,
                window_start_gte=self._to_unix_ns(start),
                window_start_lt=self._to_unix_ns(end),
                sort="asc",
                limit=50000,
            )
        )

    def list_futures_contracts(
        self,
        product_code: str,
        snapshot_date: date,
    ):
        # print(start)
        # print(type(start))

        # print(end)
        # print(type(end))
        print("calling list_futures_contracts")
        print(snapshot_date.isoformat())
        print(type(snapshot_date))
        return list(self._client.list_futures_contracts(
            product_code=product_code,
            date=self._to_date_str(snapshot_date),
        ))
    