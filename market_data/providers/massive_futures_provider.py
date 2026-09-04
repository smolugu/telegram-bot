# market_data/providers/massive_provider.py
from datetime import (
    datetime,
    date,
    time as dt_time,
    timezone,
    timedelta,
)
import time as time_module
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
    
    def get_historical_contracts(
        self,
        instrument: str,
        snapshot_dates: list[date],
    ) -> list[Contract]:

        contracts_by_ticker: dict[str, Contract] = {}

        for i, snapshot_date in enumerate(snapshot_dates):

            print(
                f"\n[{i + 1}/{len(snapshot_dates)}] "
                f"Getting {instrument} contracts for "
                f"{snapshot_date}"
            )

            retries = 0
            max_retries = 5

            while True:

                try:

                    results = self._rest.list_futures_contracts(
                        product_code=instrument,
                        snapshot_date=snapshot_date,
                    )

                    break

                except Exception as e:

                    if "429" not in str(e):
                        raise

                    retries += 1

                    if retries > max_retries:
                        raise

                    delay = 10 * (2 ** (retries - 1))

                    print(
                        f"Rate limited (429). "
                        f"Retrying in {delay}s..."
                    )

                    time_module.sleep(delay)

            print(
                f"Received {len(results)} records"
            )

            for c in results:

                # ------------------------------------------------------
                # Only outright contracts
                # ------------------------------------------------------
                if "-" in c.ticker:
                    continue

                contract = Contract(
                    contract=c.ticker,
                    instrument=instrument,
                    contract_type="single",

                    first_trade_date=self._to_date(
                        c.first_trade_date
                    ),

                    rollover_date=None,

                    last_trade_date=self._to_date(
                        c.last_trade_date
                    ),

                    settlement_date=self._to_date(
                        c.settlement_date
                    ),

                    days_to_maturity=c.days_to_maturity,

                    active=c.active,
                )

                # ------------------------------------------------------
                # Deduplicate by ticker
                # ------------------------------------------------------
                #
                # Same contract can appear in multiple snapshots.
                #
                # Prefer the record with the earliest first_trade_date
                # if Massive gives us different metadata.
                # ------------------------------------------------------

                existing = contracts_by_ticker.get(
                    contract.contract
                )

                if existing is None:

                    contracts_by_ticker[
                        contract.contract
                    ] = contract

                else:

                    if (
                        contract.first_trade_date
                        and existing.first_trade_date
                        and contract.first_trade_date
                        < existing.first_trade_date
                    ):
                        contracts_by_ticker[
                            contract.contract
                        ] = contract

            # ----------------------------------------------------------
            # Give Massive some breathing room before next request
            # ----------------------------------------------------------

            if i < len(snapshot_dates) - 1:

                print("Waiting 10 seconds before next request...")
                time_module.sleep(10)

        contracts = list(
            contracts_by_ticker.values()
        )

        # --------------------------------------------------------------
        # Sort by expiry
        # --------------------------------------------------------------

        contracts.sort(
            key=lambda c: (
                c.last_trade_date
                if c.last_trade_date is not None
                else date.max
            )
        )

        # --------------------------------------------------------------
        # Calculate rollover dates
        # --------------------------------------------------------------

        contracts_with_rollover = []

        previous = None

        for contract in contracts:

            rollover_date = (
                previous.last_trade_date
                if previous is not None
                else None
            )

            contracts_with_rollover.append(
                Contract(
                    contract=contract.contract,
                    instrument=contract.instrument,
                    contract_type=contract.contract_type,
                    first_trade_date=contract.first_trade_date,
                    rollover_date=rollover_date,
                    last_trade_date=contract.last_trade_date,
                    settlement_date=contract.settlement_date,
                    days_to_maturity=contract.days_to_maturity,
                    active=contract.active,
                )
            )

            previous = contract

        contracts = contracts_with_rollover

        return contracts

    def get_contracts(
        self,
        instrument: str,
        snapshot_date: date,
    ) -> list[Contract]:

        results = self._rest.list_futures_contracts(
            product_code=instrument,
            snapshot_date=snapshot_date,
        )

        print(
            f"Massive returned {len(results)} "
            f"{instrument} contract records for {snapshot_date}"
        )

        contracts_by_ticker: dict[str, Contract] = {}

        for c in results:

            # ------------------------------------------------------
            # Only outright contracts
            # ------------------------------------------------------
            if "-" in c.ticker:
                continue

            contract = Contract(
                contract=c.ticker,
                instrument=instrument,
                contract_type="single",

                first_trade_date=self._to_date(
                    c.first_trade_date
                ),

                rollover_date=None,

                last_trade_date=self._to_date(
                    c.last_trade_date
                ),

                settlement_date=self._to_date(
                    c.settlement_date
                ),

                days_to_maturity=c.days_to_maturity,

                active=c.active,
            )

            contracts_by_ticker[contract.contract] = contract

        contracts = list(contracts_by_ticker.values())

        # ----------------------------------------------------------
        # Sort by last trade date
        # ----------------------------------------------------------

        contracts.sort(
            key=lambda c: (
                c.last_trade_date
                if c.last_trade_date is not None
                else date.max
            )
        )

        # ----------------------------------------------------------
        # Calculate rollover dates
        # ----------------------------------------------------------

        contracts_with_rollover = []

        previous = None

        for contract in contracts:

            rollover_date = (
                previous.last_trade_date
                if previous is not None
                else None
            )

            contracts_with_rollover.append(
                Contract(
                    contract=contract.contract,
                    instrument=contract.instrument,
                    contract_type=contract.contract_type,
                    first_trade_date=contract.first_trade_date,
                    rollover_date=rollover_date,
                    last_trade_date=contract.last_trade_date,
                    settlement_date=contract.settlement_date,
                    days_to_maturity=contract.days_to_maturity,
                    active=contract.active,
                )
            )

            previous = contract

        return contracts_with_rollover
        

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