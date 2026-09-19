from datetime import date, datetime, timedelta, timezone
import time

from framework.models.auction.engine.auction_engine import initialize_auction
from framework.models.auction.models.auction_engine import AuctionEngine
from framework.models.candle_7h import SevenHourBuilder
from framework.models.ib_continuation_candidate import IBContinuationCandidate
from framework.models.london_market_context import LondonMarketContext
from framework.models.market_context import MarketContext
from framework.models.nyam_market_context import NewYorkMarketContext
from framework.models.setup_candidate import SetupCandidate
from framework.state.weekly_state import build_weekly_state, initialize_weekly_state
from engine.helpers.atr import calculate_daily_atr
from helpers.atr import calculate_atr
from helpers.liquidity_levels import get_liquidity_values, refresh_liquidity, reset_liquidity
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

def  initialize_ping(contract_repo, candle_repo, runtime, weekday):
        print(">>> Initializing Ping")
        # update current day state from start of day to start of ping
        # update auction engine state till start of day
        # update weekly state till start of day
        print(">>> Ping start time:", runtime.start_time)
        
        start_time_ny = runtime.start_time.astimezone(NY_TZ)


        # ===========================
        # get contracts
        # ===========================
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

        day_nq_contract = nq_contract.contract
        day_es_contract = es_contract.contract
        runtime.nq_contract = day_nq_contract
        runtime.es_contract = day_es_contract

        previous_trading_day = get_previous_trading_day(
            start_time_ny
        )
        prev_day_nq_contract = contract_repo.get_front_month(
            "NQ",
            previous_trading_day,
        )

        prev_day_es_contract = contract_repo.get_front_month(
            "ES",
            previous_trading_day,
        )
        prev_day_nq_contract = prev_day_nq_contract.contract
        prev_day_es_contract = prev_day_es_contract.contract

        # ===========================
        # Initialize Daily Context - PDH/L and ATRs and LIQUIDITY levels
        # ===========================
        trading_date = get_previous_trading_day(start_time_ny)
        candle_time_ny = datetime.combine(
            trading_date,
            datetime.min.time(),
            tzinfo=NY_TZ,
        ).replace(hour=18)

        candle_time_utc = candle_time_ny.astimezone(timezone.utc)
        previous_day_nq_candle = candle_repo.get_at(
            contract=nq_contract,
            timeframe=1440,
            timestamp=candle_time_utc,
        )

        previous_day_es_candle = candle_repo.get_at(
            contract=es_contract,
            timeframe=1440,
            timestamp=candle_time_utc,
        )
        if previous_day_nq_candle is not None:
            print("nq pdh: ", previous_day_nq_candle.high)
            print("nq pdl: ", previous_day_nq_candle.low)
        if previous_day_es_candle is not None:
            print("es pdh: ", previous_day_es_candle.high)
            print("es pdl: ", previous_day_es_candle.low)
        runtime.nq_pdh=previous_day_nq_candle.high if previous_day_nq_candle else None
        runtime.nq_pdl=previous_day_nq_candle.low if previous_day_nq_candle else None
        runtime.es_pdh=previous_day_es_candle.high if previous_day_es_candle else None
        runtime.es_pdl=previous_day_es_candle.low if previous_day_es_candle else None

        # ATR using daily candles
        end_date = get_previous_trading_day(start_time_ny)
        end_time_ny = datetime.combine(
            end_date,
            datetime.min.time(),
            tzinfo=NY_TZ,
        ).replace(hour=18)

        end_time_utc = end_time_ny.astimezone(timezone.utc)
        nq_last_5_daily_candles = candle_repo.get_last_n(
            contract=nq_contract,
            timeframe=1440,
            end=end_time_utc,
            n=5,
        )
        for candle in nq_last_5_daily_candles:
            print("NQ daily candle: ", candle.timestamp, candle.open, candle.high, candle.low, candle.close)

        es_last_5_daily_candles = candle_repo.get_last_n(
            contract=es_contract,
            timeframe=1440,
            end=end_time_utc,
            n=5,
        )

        nq_atr = calculate_atr(nq_last_5_daily_candles)
        es_atr = calculate_atr(es_last_5_daily_candles)
        print("atr from daily candles: ", nq_atr, es_atr)

        # ATR block
        current_trading_date = start_time_ny.date()
        history_end_ny = datetime.combine(
            current_trading_date,
            time(17, 0),
            tzinfo=NY_TZ,
        )

        history_start_ny = history_end_ny - timedelta(days=10)

        history_start_utc=history_start_ny.astimezone(UTC_TZ)
        history_end_utc=history_end_ny.astimezone(UTC_TZ)

        nq_atr_candles=candle_repo.get_between(
            contract=nq_contract,
            timeframe=30,
            start=history_start_utc,
            end=history_end_utc,
        )

        es_atr_candles = candle_repo.get_between(
            contract=es_contract,
            timeframe=30,
            start=history_start_utc,
            end=history_end_utc,
        )
        
        runtime.nq_daily_atr = calculate_daily_atr(nq_atr_candles)
        runtime.es_daily_atr = calculate_daily_atr(es_atr_candles)

        # Initialize setup candidates
        runtime.nq_sell_candidate = SetupCandidate("buy_side", "NQ")
        runtime.nq_buy_candidate = SetupCandidate("sell_side", "NQ")
        runtime.es_sell_candidate = SetupCandidate("buy_side", "ES")
        runtime.es_buy_candidate = SetupCandidate("sell_side", "ES")

        # IB candidates 
        nq_ib_candidate = IBContinuationCandidate("NQ")
        es_ib_candidate = IBContinuationCandidate("ES")
        
        # Initialize market and session contexts
        runtime.nq_market_context = MarketContext("NQ")
        runtime.es_market_context = MarketContext("ES")
        runtime.nq_london_market_context = LondonMarketContext("NQ")
        runtime.es_london_market_context = LondonMarketContext("ES")
        runtime.nq_ny_market_context = NewYorkMarketContext("NQ")
        runtime.es_ny_market_context = NewYorkMarketContext("ES")

        # sever hour builder candles
        nq_seven_hour_builder = SevenHourBuilder("NQ")
        es_seven_hour_builder = SevenHourBuilder("ES")

        runtime.nq_market_context.set_daily_atr(runtime.nq_daily_atr)
        runtime.es_market_context.set_daily_atr(runtime.es_daily_atr)

        # update liquidity levels for the current session based on previous day's liquidity
        liquidity_nq = reset_liquidity()
        liquidity_es = reset_liquidity()
        prev_liquidity_nq = reset_liquidity()
        prev_liquidity_es = reset_liquidity()
        if prev_day_nq_contract == nq_contract:
            # if runtime.liquidity is None then populate runtime with previous day
            # liquidity
            if runtime.liquidity_nq is None:
                # get prev_day_pdh and pdl
                prev_trading_date = get_previous_trading_day(start_time_ny)
                candle_time_ny = datetime.combine(
                    prev_trading_date,
                    datetime.min.time(),
                    tzinfo=NY_TZ,
                ).replace(hour=18)
                candle_end_time_ny = candle_time_ny + timedelta(days=1)
        
                candle_time_utc = candle_time_ny.astimezone(timezone.utc)
                candle_end_time_utc = candle_end_time_ny.astimezone(timezone.utc)
                nq_candle_result = candle_repo.get_at(
                    contract=nq_contract,
                    timeframe=1440,
                    timestamp=candle_time_utc,
                )
        
                es_candle_result = candle_repo.get_at(
                    contract=es_contract,
                    timeframe=1440,
                    timestamp=candle_time_utc,
                )
                prev_nq_pdh = nq_candle_result.high if nq_candle_result else None
                prev_nq_pdl = nq_candle_result.low if nq_candle_result else None
                prev_es_pdh = es_candle_result.high if es_candle_result else None
                prev_es_pdl = es_candle_result.low if es_candle_result else None    
                print("NQ prev PDh, prev PDl:", prev_nq_pdh, prev_nq_pdl)
                print("ES prev PDh, prev PDl:", prev_es_pdh, prev_es_pdl)
                
                # prev_nq_30m = get_futures_session(nq["30m"], prev_test_date)
                
                prev_nq_30m = candle_repo.get_between(
                    contract=nq_contract,
                    timeframe=30,
                    start=candle_time_utc,
                    end=candle_end_time_utc,
                )
                # prev_nq_3m = get_futures_session(nq["3m"], prev_test_date)
                prev_nq_3m=candle_repo.get_between(
                    contract=nq_contract,
                    timeframe=3,
                    start=candle_time_utc,
                    end=candle_end_time_utc,
                )
                
                prev_es_30m = candle_repo.get_between(
                    contract=es_contract,
                    timeframe=30,
                    start=candle_time_utc,
                    end=candle_end_time_utc,
                )
                
                # prev_es_3m=candle_repo.get_between(
                #     contract=es_contract,
                #     timeframe=3,
                #     start=candle_time_utc,
                #     end=candle_end_time_utc,
                # )
                
        
                if not prev_nq_30m or not prev_es_30m:
                    print("No data available.")
                    return
                
                prev_nq_30m_closes = {
                    prev_nq_30m[i]["timestamp"]: i
                    for i in range(len(prev_nq_30m))
                }
                for candle_3m in prev_nq_3m:
                        
                    ts = candle_3m["timestamp"]
                    if ts in prev_nq_30m_closes:
                        i = prev_nq_30m_closes[ts]
                        print("Matching 30m candle found for 3m timestamp:", ts, "at index", i)
                        prev_current_30m_start = prev_nq_30m[i]["timestamp"]
                        prev_last_closed_nq = prev_nq_30m[i - 1]
                        prev_last_closed_es = prev_es_30m[i - 1]
                        if i == 1:
                            print("resetting liquidity at : ", i, ts)
                            # TODO: IMP update only swept liquidity, for example keep NYPM unswept levels for next session or day
                            prev_liquidity_nq = reset_liquidity()
                            prev_liquidity_es = reset_liquidity()
                        prev_historical_nq = prev_nq_30m[:i]
                        prev_historical_es = prev_es_30m[:i]
                        prev_last_closed_nq = prev_nq_30m[i - 1]
                        prev_last_closed_es = prev_es_30m[i - 1]
                        #  gather session liquidity
                        prev_liquidity_nq = get_liquidity_values(symbol= prev_day_nq_contract, candles_30m = prev_historical_nq, liquidity_levels=prev_liquidity_nq, current_start = prev_current_30m_start, pdh = prev_nq_pdh, pdl = prev_nq_pdl)
                        prev_liquidity_es = get_liquidity_values(symbol= prev_day_es_contract, candles_30m = prev_historical_es, liquidity_levels=prev_liquidity_es, current_start = prev_current_30m_start, pdh = prev_es_pdh, pdl = prev_es_pdl)
                        for key, level in prev_liquidity_nq.items():
                            if level["side"] == "buy_side" and level["price"] is not None:
                                if prev_last_closed_nq["high"] > level["price"]:
                                    level["swept"] = True
                            if level["side"] == "sell_side" and level["price"] is not None:
                                if prev_last_closed_nq["low"] < level["price"]:
                                    level["swept"] = True
                        for key, level in prev_liquidity_es.items():
                            if level["side"] == "buy_side" and level["price"] is not None:
                                if prev_last_closed_es["high"] > level["price"]:
                                    level["swept"] = True
                            if level["side"] == "sell_side" and level["price"] is not None:
                                if prev_last_closed_es["low"] < level["price"]:
                                    level["swept"] = True
                        print("prev_liq_nq: ", prev_liquidity_nq)
                        print("prev_liq_es: ", prev_liquidity_es)
                runtime.liquidity_nq = prev_liquidity_nq
                runtime.liquidity_es = prev_liquidity_es
                
            runtime.liquidity_nq = refresh_liquidity(liquidity_nq, runtime.liquidity_nq)
            runtime.liquidity_es = refresh_liquidity(liquidity_es, runtime.liquidity_es)
        else:
            print("No previous day liquidity available for current contracts.")
            runtime.liquidity_nq = reset_liquidity()
            runtime.liquidity_es = reset_liquidity()
            runtime.nq_auction_engine = None
            runtime.es_auction_engine = None
            runtime.nq_weekly_state = None
            runtime.es_weekly_state = None

        # ---------------------------------------------------------
        # Initialize Auction Engine
        # ---------------------------------------------------------
        nq_1h_candles=None
        nq_1d_auction=None
        es_1h_candles=None
        es_1d_auction=None

        # if runtime auction engine is None or prev_day_nq_contract != nq_contract,
        # reset auction engine and update
        if runtime.nq_auction_engine is None:
            runtime.nq_auction_engine = AuctionEngine()
            runtime.es_auction_engine = AuctionEngine()
            current_trading_date = start_time_ny.date()
            print(">>> Resetting auction engines for new contracts")
            # initialize auction from beginning of contract to start of day at 18:00
            # and update auction engine state at the end of each 30m candle in replay or realtime
            auction_history_end_ny = datetime.combine(
                current_trading_date,
                time(17, 0),
                tzinfo=NY_TZ,
            )
            auction_start_ny_60 = auction_history_end_ny - timedelta(days=60)
            auction_start_ny_45 = auction_history_end_ny - timedelta(days=45)
            auction_start_ny_30 = auction_history_end_ny - timedelta(days=30)
            start_ny_10 = auction_history_end_ny - timedelta(days=10)

            auction_start_utc_60 = auction_start_ny_60.astimezone(UTC_TZ)
            auction_start_utc_45 = auction_start_ny_45.astimezone(UTC_TZ)
            auction_start_utc_30 = auction_start_ny_30.astimezone(UTC_TZ)
            start_utc_10 = start_ny_10.astimezone(UTC_TZ)
            start_time_utc = start_time_ny.astimezone(UTC_TZ)

            print(
                f">>> Loading auction history: "
                f"{auction_start_ny_60} → {start_time_ny}"
            )

            # NQ
            nq_1h_candles = candle_repo.get_between(
                contract=nq_contract,
                timeframe=60,
                start=start_utc_10,
                end=start_time_utc,
            )
            nq_3m_auction = candle_repo.get_between(
                contract=nq_contract,
                timeframe=3,
                start=auction_start_utc_60,
                end=start_time_utc,
            )

            nq_4h_auction = candle_repo.get_between(
                contract=nq_contract,
                timeframe=240,
                start=auction_start_utc_30,
                end=start_time_utc,
            )

            nq_7h_auction = candle_repo.get_between(
                contract=nq_contract,
                timeframe=420,
                start=auction_start_utc_45,
                end=start_time_utc,
            )

            nq_1d_auction = candle_repo.get_between(
                contract=nq_contract,
                timeframe=1440,
                start=auction_start_utc_60,
                end=start_time_utc,
            )

            # ES
            es_1h_candles = candle_repo.get_between(
                contract=es_contract,
                timeframe=60,
                start=start_utc_10,
                end=start_time_utc,
            )

            es_3m_auction = candle_repo.get_between(
                contract=es_contract,
                timeframe=3,
                start=auction_start_utc_60,
                end=start_time_utc,
            )

            es_4h_auction = candle_repo.get_between(
                contract=es_contract,
                timeframe=240,
                start=auction_start_utc_30,
                end=start_time_utc,
            )

            es_7h_auction = candle_repo.get_between(
                contract=es_contract,
                timeframe=420,
                start=auction_start_utc_45,
                end=start_time_utc,
            )

            es_1d_auction = candle_repo.get_between(
                contract=es_contract,
                timeframe=1440,
                start=auction_start_utc_60,
                end=start_time_utc,
            )

            nq_candles_for_auction = {
                "3m": nq_3m_auction,
                "4h": nq_4h_auction,
                "7h": nq_7h_auction,
                "1d": nq_1d_auction,
            }

            es_candles_for_auction = {
                "3m": es_3m_auction,
                "4h": es_4h_auction,
                "7h": es_7h_auction,
                "1d": es_1d_auction,
            }

            initialize_auction(
                runtime.nq_auction_engine,
                nq_candles_for_auction,
            )

            initialize_auction(
                runtime.es_auction_engine,
                es_candles_for_auction,
            )

            print(">>> Auction engines initialized")

        # Initialize WeeklyState
        # 1. Ping starting time replay 30m candles 18:00
        # 2. realtime 18:00 + sunday weekly open
        if weekday == 6:
            # Sunday 18:00 — weekly open
            runtime.nq_weekly_state = initialize_weekly_state("NQ")
            runtime.es_weekly_state = initialize_weekly_state("ES")
        elif runtime.nq_weekly_state is None or runtime.es_weekly_state is None:
            # initial ping start
            runtime.nq_weekly_state = initialize_weekly_state("NQ")
            runtime.es_weekly_state = initialize_weekly_state("ES")
        # build weekly state till start_time_ny date till 18:00
        if start_time_ny.hour >= 18:
            session_date = start_time_ny.date()
        else:
            session_date = start_time_ny.date() - timedelta(days=1)

        futures_session_start = datetime.combine(
            session_date,
            datetime.min.time(),
            tzinfo=NY_TZ,
        ).replace(hour=18)

        runtime.nq_weekly_state = build_weekly_state(
            nq_1d_auction,
            nq_1h_candles,
            futures_session_start,
            "NQ"
        )
        runtime.es_weekly_state = build_weekly_state(
            es_1d_auction,
            es_1h_candles,
            futures_session_start,
            "ES"
        )

        # 6. Initialize HTF builders
        # runtime.nq_d = []
        # runtime.es_d = []
        # runtime.nq_7h = []
        # runtime.es_7h = []
        # runtime.nq_4h = []
        # runtime.es_4h = []
        # runtime.nq_1h = []
        # runtime.es_1h = []
        
        # # 7. Replay today's 3m/30m candles up to start_time
        # # # 7.2 Initialize 7H builders / candidates
        # # get 30 and 3m candles from start of day to start_time
        # start_of_day_ny = datetime.combine(
        #     start_time_ny.date(),
        #     datetime.min.time(),
        #     tzinfo=NY_TZ,
        # ).replace(hour=18)
        # start_of_day_utc = start_of_day_ny.astimezone(timezone.utc)
        # start_time_utc = start_time_ny.astimezone(timezone.utc)
                                
        # prev_nq_30m = candle_repo.get_between(
        #     contract=nq_contract,
        #     timeframe=30,
        #     start=start_of_day_utc,
        #     end=start_time_utc,
        # )
        
        # prev_nq_3m=candle_repo.get_between(
        #     contract=nq_contract,
        #     timeframe=3,
        #     start=start_of_day_utc,
        #     end=start_time_utc,
        # )

        # prev_es_30m=candle_repo.get_between(
        #     contract=es_contract,
        #     timeframe=30,
        #     start=start_of_day_utc,
        #     end=start_time_utc,
        # )
        # es_30m_by_timestamp = {
        #     candle.timestamp: candle
        #     for candle in prev_es_30m
        # }
        
        # prev_es_3m=candle_repo.get_between(
        #     contract=es_contract,
        #     timeframe=3,
        #     start=start_of_day_utc,
        #     end=start_time_utc,
        # )
        # # 7. Replay today's 30m candles up to start_time

        # for candle_30m_nq in prev_nq_30m:
        #     if candle_30m_nq.timestamp >= start_time_ny:
        #         break
        #     candle_30m_es = es_30m_by_timestamp.get(
        #         candle_30m_nq.timestamp
        #     )

        #     if candle_30m_es is None:
        #         continue
        #     current_30m_start = candle_30m_nq.timestamp + timedelta(minutes=30)

        #     detect_ping(
        #         runtime=runtime,
        #         candle_repo=candle_repo,
        #         candle_30m_nq=candle_30m_nq,
        #         candle_30m_es=candle_30m_es,
        #         current_30m_start=current_30m_start
        #     )

        print(">>> Ping initialization placeholder complete")

        # return runtime
