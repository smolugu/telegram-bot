from datetime import date

from sqlalchemy import Boolean, Date, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class ContractORM(Base):

    __tablename__ = "contracts"

    contract: Mapped[str] = mapped_column(String(10), primary_key=True)

    instrument: Mapped[str] = mapped_column(String(10), nullable=False)

    contract_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    first_trade_date: Mapped[date | None] = mapped_column(Date)

    last_trade_date: Mapped[date | None] = mapped_column(Date)

    settlement_date: Mapped[date | None] = mapped_column(Date)

    active: Mapped[bool] = mapped_column(Boolean, nullable=False)

    days_to_maturity: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        Index(
            "idx_contract_lookup",
            "instrument",
            "active",
            "last_trade_date",
        ),
    )