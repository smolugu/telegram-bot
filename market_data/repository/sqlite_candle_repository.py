# Responsibilities
# ==================================================
# The repository should only answer questions like:

# Save candles
# Get latest candle
# Get candles in a range
# Get last N candles
# =================================================

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.session import SessionLocal
from market_data.models.candle import CandleORM
from data.models.candle import Candle
from market_data.repository.candle_repository import CandleRepository


class SQLiteCandleRepository(CandleRepository):

    def __init__(self, session: Session):
        self.session = session
    @staticmethod
    def _ensure_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def save(self, candles: list[Candle]) -> None:
        """
        Insert or update candles.
        """
        print(f"Saving {len(candles)} candles")
                # candle_repo.save(candles)
        
        for candle in candles:
            self.session.merge(self._to_orm(candle))

        self.session.commit()
        count = self.session.query(CandleORM).count()
        print(self.session.bind.url)
        print("Rows after commit:", count)
        print("Save finished")

    def latest_timestamp_by_contract(
        self,
        contract: str,
        timeframe: int,
    ):

        candle = (
            self.session.query(CandleORM)
            .filter(
                CandleORM.contract == contract,
                CandleORM.timeframe == timeframe,
            )
            .order_by(CandleORM.timestamp.desc())
            .first()
        )

        if candle is None:
            return None
        print("es candle: ", candle)
        print(
            candle.timestamp,
            candle.open,
            candle.high,
            candle.low,
            candle.close,
            candle.volume,
            candle.instrument,
            candle.contract,
        )

        return self._ensure_utc(candle.timestamp)

    def latest_timestamp_by_instrument(
            self,
            instrument: str,
            timeframe: int,
        ):
    
            candle = (
                self.session.query(CandleORM)
                .filter(
                    CandleORM.instrument == instrument,
                    CandleORM.timeframe == timeframe,
                )
                .order_by(CandleORM.timestamp.desc())
                .first()
            )
    
            if candle is None:
                return None
            print("es candle: ", candle)
            print(
                candle.timestamp,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
                candle.instrument,
                candle.contract,
            )
            return self._ensure_utc(candle.timestamp)
    

    def get_last(
        self,
        contract: str,
        timeframe: int,
        limit: int,
    ) -> list[Candle]:
        """
        Returns the most recent candles ordered oldest -> newest.
        """

        stmt = (
            select(CandleORM)
            .where(CandleORM.contract == contract)
            .where(CandleORM.timeframe == timeframe)
            .order_by(CandleORM.timestamp.desc())
            .limit(limit)
        )

        rows = self.session.scalars(stmt).all()

        rows.reverse()

        return [self._to_domain(row) for row in rows]


    def get_latest_by_instrument(
        self,
        instrument: str,
        timeframe: int,
    ) -> Candle | None:

        row = (
            self.session.query(CandleORM)
            .filter(
                CandleORM.instrument == instrument,
                CandleORM.timeframe == timeframe,
            )
            .order_by(
                CandleORM.timestamp.desc(),
                CandleORM.contract.desc(),
            )
            .first()
        )

        if row is None:
            return None

        return self._to_domain(row)

    def get_between(
        self,
        contract: str,
        timeframe: int,
        start: datetime,
        end: datetime,
    ) -> list[Candle]:
        """
        Returns candles between two timestamps ordered oldest -> newest.
        """

        stmt = (
            select(CandleORM)
            .where(CandleORM.contract == contract)
            .where(CandleORM.timeframe == timeframe)
            .where(CandleORM.timestamp >= start)
            .where(CandleORM.timestamp <= end)
            .order_by(CandleORM.timestamp)
        )

        rows = self.session.scalars(stmt).all()

        return [self._to_domain(row) for row in rows]

    def get_all(
        self,
        instrument: str,
        timeframe: int,
    ) -> list[Candle]:

        rows = (
            self.session.query(CandleORM)
            .filter(
                CandleORM.instrument == instrument,
                CandleORM.timeframe == timeframe,
            )
            .order_by(CandleORM.timestamp.asc())
            .all()
        )

        return [self._to_domain(row) for row in rows]

    def get_history(
        self,
        contract: str,
        timeframe: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Candle]:

        query = (
            self.session.query(CandleORM)
            .filter(
                CandleORM.contract == contract,
                CandleORM.timeframe == timeframe,
            )
        )

        if start is not None:
            query = query.filter(
                CandleORM.timestamp >= start
            )

        if end is not None:
            query = query.filter(
                CandleORM.timestamp <= end,
            )

        rows = (
            query.order_by(CandleORM.timestamp.asc())
            .all()
        )

        return [
            self._to_domain(row)
            for row in rows
        ]

    @staticmethod
    def _to_domain(row: CandleORM) -> Candle:
        return Candle(
            instrument=row.instrument,
            timeframe=row.timeframe,
            contract=row.contract,
            timestamp=SQLiteCandleRepository._ensure_utc(row.timestamp),
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
        )

    @staticmethod
    def _to_orm(candle: Candle) -> CandleORM:
        return CandleORM(
            instrument=candle.instrument,
            timeframe=candle.timeframe,
            timestamp=candle.timestamp,
            contract=candle.contract,
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
        )