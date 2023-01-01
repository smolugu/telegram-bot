# Responsibilities
# ==================================================
# The repository should only answer questions like:

# Save candles
# Get latest candle
# Get candles in a range
# Get last N candles
# =================================================

from datetime import datetime, timezone
from sqlite3 import IntegrityError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.session import SessionLocal
# from helpers.time_windows import NY_TZ
from market_data.models.candle import CandleORM
from data.models.candle import Candle
from market_data.repository.candle_repository import CandleRepository
from zoneinfo import ZoneInfo

UTC_TZ = ZoneInfo("UTC")
NY_TZ = ZoneInfo("America/New_York")


class SQLiteCandleRepository(CandleRepository):

    def __init__(self, session: Session):
        self.session = session
    @staticmethod
    def _ensure_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    
    @staticmethod
    def _ensure_ny(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(NY_TZ)

    

    # def save(self, candles: list[Candle]) -> None:
    #     """
    #     Insert or update candles.
    #     """
    #     print(f"Saving {len(candles)} candles")
    #             # candle_repo.save(candles)
        
    #     for candle in candles:
    #         self.session.merge(self._to_orm(candle))

    #     self.session.commit()
    #     count = self.session.query(CandleORM).count()
    #     print(self.session.bind.url)
    #     print("Rows after commit:", count)
    #     print("Save finished")
    # def save(self, candles: list[Candle]) -> None:
    #     try:
    #         for candle in candles:
    #             self.session.merge(self._to_orm(candle))

    #         self.session.commit()
    #         count = self.session.query(CandleORM).count()
    #         print(self.session.bind.url)
    #         print("Rows after commit:", count)
    #         print("Save finished")

    #     except Exception:
    #         self.session.rollback()
    #         raise
    def save(self, candles: list[Candle]) -> None:
        print(f"Saving {len(candles)} candles")

        for candle in candles:
            orm_candle = self._to_orm(candle)

            existing = self.session.get(
                CandleORM,
                (
                    orm_candle.timeframe,
                    orm_candle.timestamp,
                    orm_candle.contract,
                ),
            )

            # print(
            #     "CANDLE SAVE:",
            #     orm_candle.instrument,
            #     orm_candle.timeframe,
            #     repr(orm_candle.timestamp),
            #     orm_candle.timestamp.tzinfo,
            #     orm_candle.contract,
            #     "EXISTS:",
            #     existing is not None,
            # )

            self.session.merge(orm_candle)

        # self.session.commit()
        try:
            self.session.commit()

        except IntegrityError as e:
            self.session.rollback()

            if "UNIQUE constraint failed: candles.timeframe, candles.timestamp, candles.contract" in str(e):
                print(
                    ">>> Duplicate candle detected; "
                    "skipping insert and continuing"
                )
                return

            raise

        count = self.session.query(CandleORM).count()
        print(self.session.bind.url)
        print("Rows after commit:", count)
        print("Save finished")

    
    def latest_candle_by_instrument(
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
            .order_by(CandleORM.timestamp.desc())
            .first()
        )

        if row is None:
            return None

        return self._to_domain(row)
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
    
    def exists(
        self,
        contract: str,
        timeframe: int,
        timestamp: datetime,
    ) -> bool:

        stmt = (
            select(CandleORM.timestamp)
            .where(CandleORM.contract == contract)
            .where(CandleORM.timeframe == timeframe)
            .where(CandleORM.timestamp == timestamp)
            .limit(1)
        )

        return self.session.scalar(stmt) is not None
    
    def get_time_range(
        self,
        contract: str,
        timeframe: int,
    ) -> tuple[datetime | None, datetime | None]:

        first_stmt = (
            select(CandleORM.timestamp)
            .where(CandleORM.contract == contract)
            .where(CandleORM.timeframe == timeframe)
            .order_by(CandleORM.timestamp.asc())
            .limit(1)
        )

        last_stmt = (
            select(CandleORM.timestamp)
            .where(CandleORM.contract == contract)
            .where(CandleORM.timeframe == timeframe)
            .order_by(CandleORM.timestamp.desc())
            .limit(1)
        )

        first_timestamp = self.session.scalar(first_stmt)
        last_timestamp = self.session.scalar(last_stmt)

        if first_timestamp is not None and first_timestamp.tzinfo is None:
            first_timestamp = first_timestamp.replace(tzinfo=UTC_TZ)

        if last_timestamp is not None and last_timestamp.tzinfo is None:
            last_timestamp = last_timestamp.replace(tzinfo=UTC_TZ)

        return first_timestamp, last_timestamp


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


    def get_last_n(
        self,
        contract: str,
        timeframe: int,
        end: datetime,
        n: int,
    ) -> list[Candle]:

        stmt = (
            select(CandleORM)
            .where(CandleORM.contract == contract)
            .where(CandleORM.timeframe == timeframe)
            .where(CandleORM.timestamp < end)
            .order_by(CandleORM.timestamp.desc())
            .limit(n)
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

    def get_at(
        self,
        contract: str,
        timeframe: int,
        timestamp: datetime,
    ) -> Candle | None:

        stmt = (
            select(CandleORM)
            .where(CandleORM.contract == contract)
            .where(CandleORM.timeframe == timeframe)
            .where(CandleORM.timestamp == timestamp)
        )

        row = self.session.scalar(stmt)

        if row is None:
            return None

        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: CandleORM) -> Candle:
        
        return Candle(
            instrument=row.instrument,
            timeframe=row.timeframe,
            contract=row.contract,
            timestamp=SQLiteCandleRepository._ensure_ny(row.timestamp),
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