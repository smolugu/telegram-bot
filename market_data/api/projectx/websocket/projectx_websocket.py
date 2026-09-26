from datetime import datetime, timedelta, timezone
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
        self._realtime_start: datetime | None = None
        self._last_trade_received_at = None
        self._subscribed_contracts: set[str] = set()
        self._watchdog_thread = None
        self._watchdog_stop = threading.Event()

        self._connection = None
        self._connected = threading.Event()
        self._trade_event_count = 0

    @property
    def realtime_start(self) -> datetime:
        if self._realtime_start is None:
            raise RuntimeError(
                "Realtime connection has not been established"
            )

        return self._realtime_start
    
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
        self._start_watchdog()

    def _on_open(self):
        self._realtime_start = datetime.now(timezone.utc)

        print("ProjectX market hub connected")
        print(f"Realtime start: {self._realtime_start}")

        self._connected.set()

    # def _on_close(self):

    #     print("ProjectX market hub disconnected")

    #     self._connected.clear()
    def _on_close(self):
        print("ProjectX market hub disconnected")
        self._connected.clear()

        threading.Thread(
            target=self._reconnect,
            daemon=True,
        ).start()
    def _reconnect(self):
        print(">>> ProjectX WebSocket reconnecting...")

        try:
            self.connect()

            print(">>> ProjectX WebSocket reconnected")

            for contract_id in self._subscribed_contracts:
                self.subscribe_trades(contract_id)

        except Exception as e:
            print(f">>> ProjectX WebSocket reconnect failed: {e}")
    def test_force_disconnect(self):
        print(">>> TEST: Forcing ProjectX WebSocket disconnect...")

        if self._connection is not None:
            self._connection.stop()
        else:
            print(">>> TEST: No WebSocket connection exists")
    def _on_error(self, error):

        print(
            f"ProjectX market hub error: {error}"
        )

    def _on_gateway_trade(self, *args):
        self._last_trade_received_at = datetime.now(timezone.utc)

        # print(
        #     f"GatewayTrade received at "
        #     f"{datetime.now(timezone.utc)}"
        # )

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
            self._trade_event_count += 1
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

            # print(trade)
            if self._trade_event_count % 500 == 0:
                print(trade)
            if self._on_trade is not None:
                self._on_trade(trade)

    # def subscribe_trades(self, contract_id: str) -> None:

    #     if not self._connected.is_set():
    #         raise RuntimeError(
    #             "WebSocket is not ready"
    #         )

    #     print(
    #         f"Subscribing to trades: {contract_id}"
    #     )

    #     self._connection.invoke(
    #         "SubscribeContractTrades",
    #         [contract_id],
    #     )

    #     print(
    #         f"Trade subscription sent: {contract_id}"
    #     )
    def _watchdog_loop(self) -> None:

        while not self._watchdog_stop.wait(timeout=30):

            if not self._connected.is_set():
                continue

            if self._last_trade_received_at is None:
                continue

            elapsed = (
                datetime.now(timezone.utc)
                - self._last_trade_received_at
            )

            if elapsed > timedelta(minutes=2):

                print(
                    f">>> ProjectX WS stale: "
                    f"no GatewayTrade for {elapsed}"
                )

                self._resubscribe_trades()
    def _start_watchdog(self) -> None:

        if self._watchdog_thread is not None:
            return

        self._watchdog_stop.clear()

        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            daemon=True,
        )

        self._watchdog_thread.start()

        print("ProjectX WebSocket watchdog started")

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

        self._subscribed_contracts.add(contract_id)

        print(
            f"Trade subscription sent: {contract_id}"
        )

    def _resubscribe_trades(
        self,
    ) -> None:

        if not self._connected.is_set():
            print("Cannot resubscribe: WebSocket is not connected")
            return

        print(">>> Resubscribing to ProjectX trades")

        for contract_id in self._subscribed_contracts:
            print(
                f">>> Resubscribing trades: {contract_id}"
            )

            self._connection.invoke(
                "SubscribeContractTrades",
                [contract_id],
            )

            print(
                f">>> Resubscription sent: {contract_id}"
            )
    # def disconnect(self) -> None:

    #     if self._connection is not None:

    #         print(
    #             "Disconnecting ProjectX market hub..."
    #         )

    #         self._connection.stop()

    #         self._connection = None
    #         self._connected.clear()
    def disconnect(self) -> None:

        self._watchdog_stop.set()

        if self._connection is not None:

            print(
                "Disconnecting ProjectX market hub..."
            )

            self._connection.stop()

            self._connection = None
            self._connected.clear()