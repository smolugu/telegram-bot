from datetime import datetime, timezone

from data.models.candle import Candle
from data.models.contract import Contract
from market_data.providers.futures_provider import FuturesProvider
from market_data.api.projectx.rest.projectx_rest import ProjectXREST
from market_data.contracts.contracts_mapper import ContractMapper


class ProjectXFuturesProvider(FuturesProvider):

    def __init__(
        self,
        rest: ProjectXREST,
        contract_mapper: ContractMapper,
    ):
        self._rest = rest
        self._contract_mapper = contract_mapper

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    def get_history(
        self,
        instrument: str,
        contract: str,
        timeframe: int,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:

        projectx_contract_id = (
            self._contract_mapper.to_projectx(contract)
        )

        print(
            f"ProjectX history: "
            f"{contract} → {projectx_contract_id}"
        )

        results = self._rest.retrieve_bars(
            contract_id=projectx_contract_id,
            start=start,
            end=end,
        )
        

        candles = []
        bars = results.get("bars") or []

        # for bar in bars:

        # for bar in results.get("bars", []):
        for bar in bars:

            candles.append(
                Candle(
                    instrument=instrument,
                    timeframe=timeframe,
                    timestamp=self._parse_timestamp(
                        bar["t"]
                    ),
                    contract=contract,
                    open=bar["o"],
                    high=bar["h"],
                    low=bar["l"],
                    close=bar["c"],
                    volume=bar["v"],
                )
            )
        # candles.sort(key=lambda c: c.timestamp)
        
        new_candles = [
            candle
            for candle in candles
            if candle.timestamp >= start
        ]

        new_candles.sort(
            key=lambda candle: candle.timestamp
        )

        # if new_candles:
        #     candle_repo.save(new_candles)
        print(
            f"ProjectX returned "
            f"{len(candles)} candles"
        )

        return candles

    def get_contracts(
        self,
        instrument: str,
        snapshot_date,
    ) -> list[Contract]:

        raise NotImplementedError(
            "ProjectX contract discovery will be implemented separately."
        )

    def resolve_contract(
        self,
        contract: str,
    ) -> str:

        # ----------------------------------------------------------
        # 1. Check whether we already have the mapping
        # ----------------------------------------------------------

        try:
            return self._contract_mapper.to_projectx(contract)
        except ValueError:
            pass

        # ----------------------------------------------------------
        # 2. Search ProjectX
        # ----------------------------------------------------------

        result = self._rest.search_contracts(
            search_text=contract,
            live=False,
        )

        if not result.get("success"):
            raise RuntimeError(
                f"ProjectX contract search failed for {contract}: "
                f"{result.get('errorCode')} "
                f"{result.get('errorMessage')}"
            )

        matches = result.get("contracts", [])

        # ----------------------------------------------------------
        # 3. Find exact contract
        # ----------------------------------------------------------

        for match in matches:

            if match.get("name") != contract:
                continue

            projectx_contract_id = match.get("id")

            if not projectx_contract_id:
                raise RuntimeError(
                    f"ProjectX returned no ID for contract {contract}"
                )

            # ------------------------------------------------------
            # 4. Store mapping
            # ------------------------------------------------------

            self._contract_mapper.add(
                internal_contract=contract,
                projectx_contract_id=projectx_contract_id,
            )

            print(
                f"Contract mapping: "
                f"{contract} → {projectx_contract_id}"
            )

            return projectx_contract_id

        raise ValueError(
            f"No exact ProjectX contract match found for {contract}"
        )