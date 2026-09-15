from datetime import date, datetime, timedelta, timezone
import time

from data.models.runtime_state import PingRuntime
from engine.detect_ping import detect_ping
from framework.models.auction.engine.auction_engine import initialize_auction
from framework.models.auction.models.auction_engine import AuctionEngine
from framework.models.london_market_context import LondonMarketContext
from framework.models.market_context import MarketContext
from framework.models.nyam_market_context import NewYorkMarketContext
from framework.state.weekly_state import build_weekly_state
from engine.helpers.atr import calculate_daily_atr
from helpers.atr import calculate_atr
from helpers.liquidity_levels import get_liquidity_values, reset_liquidity
from market_data.candle_builder.htf_candle_builder import NY_TZ, UTC_TZ

def get_previous_trading_day(start_time_ny: datetime) -> date:

    if start_time_ny.hour >= 18:
        session_date = start_time_ny.date()
    else:
        session_date = start_time_ny.date() - timedelta(days=1)

    previous_trading_day = session_date

    while previous_trading_day.weekday() >= 5:
        previous_trading_day -= timedelta(days=1)

    return previous_trading_day

def  start_ping_flow(start_time, contract_repo, candle_repo):
        print(">>> starting Ping Flow")
        print(">>> Ping start time:", start_time)
        if start_time.tzinfo is None:
            raise ValueError("Ping start_time must be timezone-aware")
        start_time_ny = start_time.astimezone(NY_TZ)
        
        runtime = PingRuntime()
        runtime.start_time = start_time_ny
        # get active contract info
        # ---------------------------------------------------------

        nq_contract = contract_repo.get_front_month(
            "NQ",
            start_time_ny.date(),
        )

        es_contract = contract_repo.get_front_month(
            "ES",
            start_time_ny.date(),
        )

        if nq_contract is None or es_contract is None:
            raise RuntimeError(
                "Unable to determine front-month contract"
            )

        nq_contract = nq_contract.contract
        es_contract = es_contract.contract

        
        # 7. Replay today's 3m/30m candles up to start_time
        # # 7.2 Initialize 7H builders / candidates
        # get 30 and 3m candles from start of day to start_time
        start_of_day_ny = datetime.combine(
            start_time_ny.date(),
            datetime.min.time(),
            tzinfo=NY_TZ,
        ).replace(hour=18)
        start_of_day_utc = start_of_day_ny.astimezone(timezone.utc)
        start_time_utc = start_time_ny.astimezone(timezone.utc)
                                
        prev_nq_30m = candle_repo.get_between(
            contract=nq_contract,
            timeframe=30,
            start=start_of_day_utc,
            end=start_time_utc,
        )
        
        prev_nq_3m=candle_repo.get_between(
            contract=nq_contract,
            timeframe=3,
            start=start_of_day_utc,
            end=start_time_utc,
        )

        prev_es_30m=candle_repo.get_between(
            contract=es_contract,
            timeframe=30,
            start=start_of_day_utc,
            end=start_time_utc,
        )
        es_30m_by_timestamp = {
            candle.timestamp: candle
            for candle in prev_es_30m
        }
        
        prev_es_3m=candle_repo.get_between(
            contract=es_contract,
            timeframe=3,
            start=start_of_day_utc,
            end=start_time_utc,
        )
        # 7. Replay today's 30m candles up to start_time

        for candle_30m_nq in prev_nq_30m:
            if candle_30m_nq.timestamp >= start_time_ny:
                break
            candle_30m_es = es_30m_by_timestamp.get(
                candle_30m_nq.timestamp
            )

            if candle_30m_es is None:
                continue
            current_30m_start = candle_30m_nq.timestamp + timedelta(minutes=30)

            detect_ping(
                runtime=runtime,
                candle_repo=candle_repo,
                contract_repo=contract_repo,
                candle_30m_nq=candle_30m_nq,
                candle_30m_es=candle_30m_es,
                current_30m_start=current_30m_start
            )

        print(">>> Ping initialization placeholder complete")

        return runtime
