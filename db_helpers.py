# from sqlalchemy import select
# from database import SessionLocal
# from models import ContractORM


from sqlalchemy import select

from database.session import SessionLocal
from market_data.models.contract import ContractORM


def check_contract_order():

    with SessionLocal() as session:

        contracts = session.scalars(
            select(ContractORM)
            .where(
                ~ContractORM.contract.contains("-")
            )
            .order_by(
                ContractORM.instrument,
                ContractORM.last_trade_date,
            )
        ).all()

        current_instrument = None
        previous_last_trade = None

        for contract in contracts:

            if contract.instrument != current_instrument:
                print()
                print("=" * 60)
                print(contract.instrument)
                print("=" * 60)

                current_instrument = contract.instrument
                previous_last_trade = None

            print(
                f"{contract.contract:8} "
                f"first={contract.first_trade_date} "
                f"last={contract.last_trade_date}"
            )

            if (
                previous_last_trade is not None
                and contract.last_trade_date < previous_last_trade
            ):
                print(
                    "  *** ORDER ERROR ***"
                )

            previous_last_trade = (
                contract.last_trade_date
            )


if __name__ == "__main__":
    check_contract_order()