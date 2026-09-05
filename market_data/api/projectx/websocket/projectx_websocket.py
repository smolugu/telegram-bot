from datetime import datetime, timezone
import logging
import threading
from typing import Callable

from signalrcore.hub_connection_builder import HubConnectionBuilder
from signalrcore.types import HttpTransportType
from data.models.trade import Trade
from market_data.contracts.contracts_mapper import ContractMapper
from market_data.repository.contract_repository import ContractRepository


class ProjectXWebSocket:

    _MARKET_HUB_URL = "https://rtc.topstepx.com/hubs/market"

    def __init__(
            self, 
            token: str, 
            contract_mapper: ContractMapper,
            contract_repo: ContractRepository,
            on_trade: Callable[[Trade], None] | None = None,
            on_connected: Callable[[datetime], None] | None = None,
        ):
        self._token = token
        self._contract_mapper = contract_mapper
        self._contract_repo = contract_repo
        self._on_trade = on_trade
        self._on_connected = on_connected

        self._connection = None
        self._connected = threading.Event()

    def connect(self) -> None:

        print("Connecting to ProjectX market hub...")

        self._connection = (
            HubConnectionBuilder()
            .with_url(
                self._MARKET_HUB_URL,
                options={
                    "access_token_factory": lambda: self._token,
                    "skip_negotiation": True,
                    "transport": HttpTransportType.web_sockets,
                },
            )
            # .configure_logging(
            #     logging.DEBUG,
            #     socket_trace=False,
            # )
            .build()
        )

        self._connection.on_open(
            self._on_open
        )

        self._connection.on_close(
            self._on_close
        )

        self._connection.on_error(
            self._on_error
        )

        self._connection.on(
            "GatewayTrade",
            self._on_gateway_trade,
        )

        print("Starting SignalR connection...")

        result = self._connection.start()

        print(f"SignalR start() returned: {result}")

        if not self._connected.wait(timeout=10):
            raise RuntimeError(
                "ProjectX market hub did not become ready "
                "within 10 seconds"
            )

    def _on_open(self):
        realtime_start = datetime.now(timezone.utc)

        print("ProjectX market hub connected")
        print(f"Realtime start: {realtime_start}")

        if self._on_connected is not None:
            self._on_connected(realtime_start)

        self._connected.set()

    def _on_close(self):

        print("ProjectX market hub disconnected")

        self._connected.clear()

    def _on_error(self, error):

        print(
            f"ProjectX market hub error: {error}"
        )

    def _on_gateway_trade(self, *args):

        contract_id, trades = args[0]

        internal_contract = (
            self._contract_mapper.from_projectx(
                contract_id
            )
        )

        contract = self._contract_repo.get(
            internal_contract
        )

        if contract is None:
            print(
                f"No contract found in repository: "
                f"{internal_contract}"
            )
            return

        for data in trades:

            trade = Trade(
                instrument=contract.instrument,
                contract=internal_contract,
                timestamp=datetime.fromisoformat(
                    data["timestamp"]
                ).astimezone(timezone.utc),
                price=float(data["price"]),
                volume=int(data["volume"]),
                side=int(data["type"]),
            )

            print(trade)
            if self._on_trade is not None:
                self._on_trade(trade)

    def subscribe_trades(self, contract_id: str) -> None:

        if not self._connected.is_set():
            raise RuntimeError(
                "WebSocket is not ready"
            )

        print(
            f"Subscribing to trades: {contract_id}"
        )

        self._connection.invoke(
            "SubscribeContractTrades",
            [contract_id],
        )

        print(
            f"Trade subscription sent: {contract_id}"
        )

    def disconnect(self) -> None:

        if self._connection is not None:

            print(
                "Disconnecting ProjectX market hub..."
            )

            self._connection.stop()

            self._connection = None
            self._connected.clear()