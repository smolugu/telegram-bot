# Final Engine Struncture
# MarketContext
    # 7H Candles
    # IB levels
    # session range
    # ATR
    # expansion metrics
    # day type
# Execution Engine
    # Reversal
        # sweep
        # SMT
        # OB
        # imbalance
    # Continuation
        # IB Breakouts and Acceptance
        # IB metrics
# Trading Engine
    # entry
    # stop
    # TP
    # alerts




# Context Layer
#     7H candles
#     IB levels
#     wick windows
#     ATR

# Structure Layer
#     sweeps
#     SMT

# Execution Layer
#     OB
#     imbalance


# entry sequence
# 7H wick window
# ↓
# liquidity sweep
# ↓
# SMT
# ↓
# 30m OB
# ↓
# 3m imbalance
# ↓
# 90-minute timing filter
# ↓
# entry