def initialize_delivery_state():

    return {
        "day_start": None,
        "day_open": None,
        "price_location": None,      # above | below

        "bullish_cisd_1h": None,
        "bearish_cisd_1h": None,

        "bullish_cisd_30m": None,
        "bearish_cisd_30m": None,

        "bullish_cisd_15m": None,
        "bearish_cisd_15m": None,

        "bullish_fvg_1h": None,
        "bearish_fvg_1h": None,
        "bullish_fvg_30m": None,
        "bearish_fvg_30m": None,
        "bullish_fvg_15m": None,
        "bearish_fvg_15m": None,

        "smt_day": None,
        "smt_7h": None,
        "smt_4h": None,

        "bias": None,
        "bias_reason": None,
    }