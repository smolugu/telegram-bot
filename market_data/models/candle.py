from sqlalchemy import (
    String,
    Integer,
    Float,
    DateTime,
    Index,
)

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from database.base import Base


class CandleORM(Base):

    __tablename__ = "candles"

    instrument: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    timeframe: Mapped[int] = mapped_column(primary_key=True)

    timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
    )

    contract: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
    )
    open: Mapped[float] = mapped_column(Float)

    high: Mapped[float] = mapped_column(Float)

    low: Mapped[float] = mapped_column(Float)

    close: Mapped[float] = mapped_column(Float)

    volume: Mapped[int] = mapped_column(Integer)


Index(
    "idx_candles_lookup",
    CandleORM.instrument,
    CandleORM.timeframe,
    CandleORM.timestamp,
)

Index(
    "idx_candles_contract",
    CandleORM.contract,
    CandleORM.timeframe,
    CandleORM.timestamp,
)