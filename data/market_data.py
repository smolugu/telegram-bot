from datetime import datetime

import yfinance as yf
import pandas as pd


# ---------------------------
# Public API
# ---------------------------

def fetch_market_data():

    nq = fetch_symbol_data("NQ=F")
    es = fetch_symbol_data("ES=F")

    # If weekend or no data, skip cycle
    if not nq or not es:
        return None

    daily = fetch_daily_data("NQ=F")

    if not daily:
        return None

    return {
        "NQ": nq,
        "ES": es,
        "daily": daily,
        "current_price": nq["30m"][-1]["close"]
    }


# ---------------------------
# Symbol Data
# ---------------------------

def fetch_symbol_data(symbol: str):

    ticker = yf.Ticker(symbol)

    # 30m
    # df_30m = ticker.history(interval="30m", period="7d")

    # 1h
    df_1h = ticker.history(interval="60m", period="14d")

    # 1m → aggregate to 3m
    df_1m = ticker.history(interval="1m", period="7d")
    # 5m → aggregate to 30m
    df_5m = ticker.history(interval="5m", period="7d")

    if df_1h.empty or df_1m.empty or df_5m.empty:
        print(f"No intraday data for {symbol}. Possibly weekend.")
        return None

    df_3m = resample_to_3m(df_1m)
    df_30m = resample_to_30m(df_5m)
    df_15m = resample_to_15m(df_5m)

    return {
        "15m": format_df(df_15m),
        "30m": format_df(df_30m),
        "1h": format_df(df_1h),
        "3m": format_df(df_3m),
        "protected_high": None,
        "protected_low": None
    }

# ---------------------------
# Session Data
# ---------------------------
# using pandas
# def session_high_low(df, start, end):

#     session = df.between_time(start, end)

#     if session.empty:
#         return None, None

#     return session["High"].max(), session["Low"].min()


from datetime import datetime

def asia_session_high_low(candles, last_closed_candle_ts):

    last_closed_dt = datetime.fromisoformat(last_closed_candle_ts)
    hour_last_closed = last_closed_dt.hour

    # Asia session must be finished
    if hour_last_closed < 2:
        return None, None

    # Do not use previous day's session after reset
    if hour_last_closed >= 16:
        return None, None

    session = []

    for c in candles:

        dt = datetime.fromisoformat(c["timestamp"])
        hour = dt.hour

        if hour >= 20 or hour < 2:
            session.append(c)

    if not session:
        return None, None

    high = max(c["high"] for c in session)
    low = min(c["low"] for c in session)

    return high, low

def session_high_low(candles, start_hour, end_hour, last_closed_candle_ts):

    session = []
    last_closed_dt = datetime.fromisoformat(last_closed_candle_ts)
    hour_last_closed = last_closed_dt.hour
    if hour_last_closed < end_hour:
        return None, None
    # do not return session highs and lows after 18:00 reset
    if hour_last_closed >= 16:
        return None, None
    for c in candles:

        dt = datetime.fromisoformat(c["timestamp"])
        hour = dt.hour

        if start_hour <= hour < end_hour:
            session.append(c)

    if not session:
        return None, None

    high = max(c["high"] for c in session)
    low = min(c["low"] for c in session)

    return high, low


# ---------------------------
# Daily Data
# ---------------------------

def get_pdh_pdl_fixed_date(current_date, symbol="NQ=F"):
    ticker = yf.Ticker(symbol)
    df_1d = ticker.history(interval="1d", period="10d")

    test_date = pd.Timestamp(current_date).tz_localize(df_1d.index.tz)

    prev_day = df_1d.loc[df_1d.index < test_date].iloc[-1]

    return float(prev_day["High"]), float(prev_day["Low"])

def get_pdh_pdl_fixed_date2(current_date, symbol="NQ=F"):
    ticker = yf.Ticker(symbol)
    df_1d = ticker.history(interval="1d", period="10d")

    prev_day = df_1d.loc[df_1d.index < pd.Timestamp(current_date)].iloc[-1]

    pdh = prev_day["High"]
    pdl = prev_day["Low"]

    return pdh, pdl

def get_pdh_pdl(symbol: str):
    ticker = yf.Ticker(symbol)

    df = ticker.history(interval="1d", period="3d")

    if len(df) < 2:
        return None, None

    pdh = df.iloc[1]["High"]
    pdl = df.iloc[1]["Low"]

    return pdh, pdl

def fetch_daily_data(symbol: str):

    ticker = yf.Ticker(symbol)

    df_daily = ticker.history(interval="1d", period="10d")

    if df_daily.empty:
        return None

    return format_df(df_daily)


# ---------------------------
# Resample 1m → 3m
# ---------------------------

def resample_to_3m(df):

    df = df.copy()
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df.resample("3min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })

    df = df.dropna()

    return df

def resample_to_30m(df):

    df = df.copy()
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df.resample("30min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })

    df = df.dropna()

    return df

def resample_to_15m(df):

    df = df.copy()
    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df.resample("15min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })

    df = df.dropna()

    return df


# ---------------------------
# Format DataFrame
# ---------------------------

def format_df(df):

    df = df.reset_index()

    candles = [
        {
            "timestamp": row[df.columns[0]].isoformat(),
            "open": row["Open"],
            "high": row["High"],
            "low": row["Low"],
            "close": row["Close"]
        }
        for _, row in df.iterrows()
    ]

    # 🔒 Remove last candle (likely incomplete)
    if len(candles) > 1:
        candles = candles[:-1]

    return candles



def fetch_symbol_data_safe(symbol):
    try:
        return fetch_symbol_data(symbol)
    except Exception as e:
        print(f"Data fetch failed for {symbol}: {e}")
        return None
