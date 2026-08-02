from abc import ABC, abstractmethod
from datetime import date, datetime

from market_data.models.candle import Candle
from market_data.models.contract import Contract


class BaseProvider(ABC):

    @abstractmethod
    def get_history(
        self,
        contract: str,
        start: datetime,
        end: datetime,
        timeframe: int,
    ) -> list[Candle]:
        pass

    @abstractmethod
    def get_contracts(
        self,
        instrument: str,
        snapshot_date: date,
    ) -> list[Contract]:
        pass