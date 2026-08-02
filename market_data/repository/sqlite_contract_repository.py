from sqlalchemy import select
from sqlalchemy.orm import Session

from market_data.models.contract import ContractORM
from data.models.contract import Contract

from .contract_repository import ContractRepository


class SQLiteContractRepository(ContractRepository):

    def __init__(self, session: Session):
        self.session = session

    def save(self, contracts: list[Contract]) -> None:
        
        for contract in contracts:
            # print("1000")
            # print(type(contract.first_trade_date), contract.first_trade_date)
            # print(type(contract.last_trade_date), contract.last_trade_date)
            # print(type(contract.settlement_date), contract.settlement_date)
            self.session.merge(self._to_orm(contract))

        self.session.commit()

    def get(self, contract: str) -> Contract | None:

        stmt = (
            select(ContractORM)
            .where(ContractORM.contract == contract)
        )

        row = self.session.scalar(stmt)

        if row is None:
            return None

        return self._to_domain(row)

    def get_front_month(
        self,
        instrument: str,
    ) -> Contract | None:

        stmt = (
            select(ContractORM)
            .where(ContractORM.instrument == instrument)
            .where(ContractORM.active.is_(True))
            .where(ContractORM.contract_type == "single")
            .order_by(ContractORM.last_trade_date)
            .limit(1)
        )

        row = self.session.scalar(stmt)

        if row is None:
            return None

        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: ContractORM) -> Contract:
        return Contract(
            contract=row.contract,
            instrument=row.instrument,
            contract_type=row.contract_type,
            first_trade_date=row.first_trade_date,
            last_trade_date=row.last_trade_date,
            settlement_date=row.settlement_date,
            days_to_maturity=row.days_to_maturity,
            active=row.active,
        )

    @staticmethod
    def _to_orm(contract: Contract) -> ContractORM:
        return ContractORM(
            contract=contract.contract,
            instrument=contract.instrument,
            contract_type=contract.contract_type,
            first_trade_date=contract.first_trade_date,
            last_trade_date=contract.last_trade_date,
            settlement_date=contract.settlement_date,
            days_to_maturity=contract.days_to_maturity,
            active=contract.active,
        )

    def get_all(
        self,
        instrument: str,
    ) -> list[Contract]:

        rows = (
            self.session.query(ContractORM)
            .filter(ContractORM.instrument == instrument)
            .order_by(ContractORM.last_trade_date)
            .all()
        )

        return [self._to_domain(row) for row in rows]