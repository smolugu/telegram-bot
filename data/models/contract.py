from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class Contract:
    contract: str
    instrument: str
    contract_type: str
    first_trade_date: date | None
    rollover_date: date | None
    last_trade_date: date | None
    settlement_date: date | None
    days_to_maturity: int | None
    active: bool