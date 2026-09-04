from data.models.contract import Contract


def set_rollover_dates(
    contracts: list[Contract],
) -> None:

    previous = None

    for contract in contracts:

        if previous is None:
            contract.rollover_date = None

        else:
            contract.rollover_date = (
                previous.last_trade_date
            )

        previous = contract