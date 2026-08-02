from abc import ABC, abstractmethod
from datetime import date, datetime

from data.models.candle import Candle
from data.models.contract import Contract


class FuturesProvider(ABC):

    @abstractmethod
    def get_contracts(
        self,
        instrument: str,
        snapshot_date: date,
    ) -> list[Contract]:
        """
        Returns all futures contracts for an instrument on the given snapshot date.
        """
        pass

    @abstractmethod
    def get_history(
        self,
        contract: str,
        timeframe: int,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        pass

    