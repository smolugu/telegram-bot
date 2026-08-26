from framework.models.auction.detector.collect_levels import collect_levels
from framework.models.auction.detector.detect_fvg import detect_fvg
from framework.models.auction.detector.detect_swings import detect_swings
from framework.models.auction.detector.detect_vi import detect_vi
from framework.models.auction.engine.auction_context import build_auction_context
from framework.models.auction.engine.add_update_levels import update_historical_level_state


def initialize_auction_engine(auction_engine, candles_for_auction):
    """
    Initialize the Auction Engine from historical HTF candles.

    Responsibilities:
        1. Detect HTF levels.
        2. Collect all levels.
        3. Update historical level status.
        4. Build AuctionContext.
        5. Calculate auction progress.
        6. Build AuctionStatus.

    Returns:
        AuctionEngine
    """

    # ---------------------------------------------------------
    # 1. Get historical candles
    # ---------------------------------------------------------

    daily_candles = candles_for_auction.get("1d", [])
    h7_candles = candles_for_auction.get("7h", [])
    h4_candles = candles_for_auction.get("4h", [])

    # ---------------------------------------------------------
    # 2. Detect HTF levels
    # ---------------------------------------------------------

    daily_swings = detect_swings(daily_candles,timeframe="1d",)
    daily_fvgs = detect_fvg(daily_candles,timeframe="1d",)
    daily_vis = detect_vi(daily_candles,timeframe="1d",)

    h7_swings = detect_swings(h7_candles,timeframe="7h",)
    h7_fvgs = detect_fvg(h7_candles,timeframe="7h",)
    h7_vis = detect_vi(h7_candles,timeframe="7h",)

    # for candle in h4_candles:
    #     if candle.timestamp.date().isoformat() == "2026-08-16":
    #         print("+=+=+=")
    #         print(
    #             candle.timestamp,
    #             candle.open,
    #             candle.high,
    #             candle.low,
    #             candle.close
    #         )
    h4_swings = detect_swings(h4_candles,timeframe="4h",)
    h4_fvgs = detect_fvg(h4_candles,timeframe="4h",)
    h4_vis = detect_vi(h4_candles,timeframe="4h",)

    # ---------------------------------------------------------
    # 3. Collect all HTF levels
    # ---------------------------------------------------------
    print("4h swings in initialize auction: ", h4_swings)
    levels = collect_levels(
        daily_swings=daily_swings,
        daily_fvgs=daily_fvgs,
        daily_vis=daily_vis,

        h7_swings=h7_swings,
        h7_fvgs=h7_fvgs,
        h7_vis=h7_vis,

        h4_swings=h4_swings,
        h4_fvgs=h4_fvgs,
        h4_vis=h4_vis,
    )
    print("levels before: ", levels)
    levels = update_historical_level_state(levels, candles_for_auction)
    print("levels after: ", levels)
    # build auction context
    # auction_engine.auction_context = build_auction_context(levels)
    build_auction_context(levels, auction_engine)
    # print("==================================")
    # print("auction_context at initialization: ", auction_engine.context.summary())
    # set auction progress in the for loop at the end of each 30m candle

    
    # return auction_engine