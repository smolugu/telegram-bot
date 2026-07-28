from datetime import date


class FuturesProvider:

    def __init__(self, massiveClient):
        self.client = massiveClient.client

    # get_contracts()
    # get_active_contract()
    # get_bars()
    # get_quotes()
    # get_trades()
    
    def get_front_month_contract(self, product_code: str) -> str:
        today = date.today().isoformat()

        response = self.client.list_futures_contracts(
            product_code=product_code,
            date=today,
            raw=True,
        )

        data = response.json()   # or json.loads(response.data)

        singles = [
            c for c in data["results"]
            if c["type"] == "single"
            and c.get("days_to_maturity") is not None
        ]

        front = min(singles, key=lambda c: c["days_to_maturity"])

        return front["ticker"]

    def get_futures_bars(
        self,
        ticker: str,
        resolution: str,
        window_start: str,
        limit: int = 50000,
    ):
        # return list(
        #     self.client.list_futures_aggregates(
        #         ticker=ticker,
        #         resolution=resolution,
        #         window_start=window_start,
        #         limit=limit,
        #     )
        # )
        bars = list(
            self.client.list_futures_aggregates(
                ticker="NQU6",
                resolution="1hour",
                window_start_gte="2026-07-15",
                window_start_lt="2026-07-16",
                limit=100,
            )
        )

        print(len(bars))
        return bars