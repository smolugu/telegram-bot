from abc import ABC, abstractmethod
from datetime import datetime

from data.models.candle import Candle


class CandleRepository(ABC):
    """
    Abstract repository interface for candle persistence.
    """

    @abstractmethod
    def save(self, candles: list[Candle]) -> None:
        pass

    def get_time_range(
        self,
        contract: str,
        timeframe: int,
    ) -> tuple[datetime | None, datetime | None]:
        pass
    
    def exists(
        self,
        contract: str,
        timeframe: int,
        timestamp: datetime,
    ) -> bool:
        pass
    
    # @abstractmethod
    # def latest_timestamp(
    #     self,
    #     contract: str,
    #     timeframe: int,
    # ) -> datetime | None:
    #     pass
    

    @abstractmethod
    def latest_candle_by_instrument(
        self,
        instrument: str,
        timeframe: int,
    ) -> Candle | None:
        pass

    @abstractmethod
    def latest_timestamp_by_instrument(
        self,
        instrument: str,
        timeframe: int,
    ) -> datetime | None:
        pass

    @abstractmethod
    def latest_timestamp_by_contract(
        self,
        contract: str,
        timeframe: int,
    ) -> datetime | None:
        pass

    @abstractmethod
    def get_last(
        self,
        contract: str,
        timeframe: int,
        limit: int,
    ) -> list[Candle]:
        pass

    @abstractmethod
    def get_at(
        self,
        contract: str,
        timeframe: int,
        timestamp: datetime,
    ) -> Candle | None:
        pass

    @abstractmethod
    def get_last_n(
        self,
        contract: str,
        timeframe: int,
        end: datetime,
        n: int,
    ) -> list[Candle]:
        ...

    

    @abstractmethod
    def get_between(
        self,
        contract: str,
        timeframe: int,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        pass

    @abstractmethod
    def get_all(
        self,
        instrument: str,
        timeframe: int,
    ) -> list[Candle]:
        pass


    @abstractmethod
    def get_history(
        self,
        contract: str,
        timeframe: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Candle]:
        pass

    @abstractmethod
    def get_latest_by_instrument(
        self,
        instrument: str,
        timeframe: int,
    ) -> Candle | None:
        pass