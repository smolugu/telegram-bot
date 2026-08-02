# market_data/providers/massive_provider.py

from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo

from data.models.candle import Candle
from market_data.api.massive_rest import MassiveREST
from data.models.contract import Contract
from market_data.providers.futures_provider import FuturesProvider


class MassiveFuturesProvider(FuturesProvider):

    def __init__(self, rest: MassiveREST):
        self._rest = rest

    @staticmethod
    def _to_date(value: str | None) -> date | None:
        return date.fromisoformat(value) if value else None
    
    @staticmethod
    def _from_unix_ns(ns: int) -> datetime:
        return datetime.fromtimestamp(
            ns / 1_000_000_000,
            tz=timezone.utc,
        )

    def get_contracts(
        self,
        instrument: str,
        snapshot_date: date,
    ) -> list[Contract]:

        results = self._rest.list_futures_contracts(
            product_code=instrument,
            snapshot_date=snapshot_date,
        )
        print("response of list_futures_contracts")
        print(results[0])
        print(type(results))
        contracts = []

        for c in results:

            contracts.append(
                Contract(
                    contract=c.ticker,
                    instrument=instrument,
                    contract_type=c.type,
                    first_trade_date=self._to_date(c.first_trade_date),
                    last_trade_date=self._to_date(c.last_trade_date),
                    settlement_date=self._to_date(c.settlement_date),
                    days_to_maturity=c.days_to_maturity,
                    active=c.active,
                )
            )

        return contracts

    def get_history(
        self,
        instrument: str,
        contract: str,
        timeframe: int,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:

        results = self._rest.list_futures_aggregates(
            contract=contract,
            start=start,
            end=end,
        )

        candles = []
        print("attrs:")
        print(len(results))
        if len(results)>0:
            print(results[0].window_start)
            print(results[-1].window_start)

        for c in results:

            candles.append(
                Candle(
                    instrument=instrument,
                    timeframe=timeframe,
                    # timestamp = datetime.fromtimestamp(
                    #     c.timestamp / 1000,
                    #     tz=ZoneInfo("America/New_York"),
                    # ),
                    # storing timestamp in UTC by default as it is universal across all data sources
                    # change to EST only when needed on the front side
                    # timestamp=datetime.fromtimestamp(
                    #     c.timestamp / 1000,
                    #     tz=timezone.utc,
                    # ),
                    timestamp=self._from_unix_ns(c.window_start),
                    contract=contract,
                    open=c.open,
                    high=c.high,
                    low=c.low,
                    close=c.close,
                    volume=c.volume,
                )
            )

        return candles