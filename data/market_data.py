from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd


# ---------------------------
# Public API
# ---------------------------

def filter_hourly_candles(hourly_candles, current_ts):

    current_dt = datetime.fromisoformat(current_ts)

    filtered = []

    for c in hourly_candles:
        dt = datetime.fromisoformat(c["timestamp"])
    

        if dt <= current_dt:
            filtered.append(c)

    return filtered

def get_current_contract(instrument, date_str=None):
    if date_str is None:
        today = datetime.now().date()
    else:
        today = datetime.strptime(date_str, "%Y-%m-%d")
    print("month: ", today.month)
    print("day:", today.day)
    
    # Very simple quarterly logic (adjust the exact switch day if your broker rolls on a different date)
    if today.month < 3: 
        return instrument + "H26.CME"
    elif today.month == 3 and today.day < 18:
        return instrument + "H26.CME"
    elif today.month == 3 and today.day >= 18:
        return instrument + "M26.CME"
    elif today.month < 6:
        return instrument + "M26.CME"
    elif today.month == 6 and today.day < 15:
        return instrument + "M26.CME"
    elif today.month == 6 and today.day >= 15:
        return "NQU26"
    elif today.month < 9:
        return "NQU26"
    elif today.month == 9 and today.day < 15:
        return "NQU26"
    elif today.month == 9 and today.day >= 15:
        return "NQZ26"
    else: 
        return "NQZ26"
    

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
    # df_30md = ticker.history(interval="30m", period="7d")

    # 1d
    df_1d = ticker.history(interval="1d", period="14d", auto_adjust=False)
    # print("direct daily candles: ", df_1d.head(20).to_string())

    # 1h
    df_1h = ticker.history(interval="60m", period="14d")

    # 1m → aggregate to 3m
    df_1m = ticker.history(interval="1m", period="7d")
    # 5m → aggregate to 30m
    df_5m = ticker.history(interval="5m", period="7d")

    if df_1h.empty or df_1m.empty or df_5m.empty:
        print(f"No intraday data for {symbol}. Possibly weekend.")
        return None
    # print("1m candles: ", df_1m)

    date = "2026-05-18"

    filtered = df_5m.loc[date]

    candles_1800 = filtered.between_time("18:00", "23:59")
    # print("raw 5m candles for date: ", date)
    # print(candles_1800.head(50).to_string())
    df_3m = resample_to_3m(df_1m)
    # date = "2026-05-18"

    # filtered = df_3m.loc[date]

    # candles_1800 = filtered.between_time("18:00", "23:59")
    # print("3m candles all: ", df_3m)
    # print("3m candles after resample")
    # print(candles_1800.head(50).to_string())
    
    df_30m = resample_to_30m(df_5m)
    # df_30m = resample_to_30m(df_1m)
    df_15m = resample_to_15m(df_5m)
    # print("formatted candles: ", format_df(df_3m))
    # df_1d = resample_to_1d(df_5m)

    return {
        "15m": format_df(df_15m),
        "30m": format_df(df_30m),
        "1h": format_df(df_1h),
        "3m": format_df(df_3m),
        "1d": format_df(df_1d),
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


# ---------------------------
# Daily Data
# ---------------------------

def get_pdh_pdl_fixed_date(current_date, symbol="NQ=F"):
    ticker = yf.Ticker(symbol)
    # print("ticker info:", ticker.info)
    df_1d = ticker.history(interval="1d", period="10d")
    # print("daily_candles:", df_1d)

    test_date = pd.Timestamp(current_date).tz_localize(df_1d.index.tz)

    prev_day = df_1d.loc[df_1d.index < test_date].iloc[-1]

    return float(prev_day["High"]), float(prev_day["Low"])


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
    df = df.resample("3min",
        label="left",
        closed="left"
        # origin="start_day", offset="18h"
        ).agg({
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

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # # Shift 5m candles to actual opening boundary
    # df.index = df.index + pd.Timedelta(minutes=5)

    df = df.resample(
        "30min",
        # label="left",
        # closed="left",
        # origin="start_day",
        # offset="18h"
    ).agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })

    return df.dropna()

def resample_to_1d(df):

    df = df.copy()

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # # Shift 5m candles to actual opening boundary
    # df.index = df.index + pd.Timedelta(minutes=5)

    df = df.resample(
        "720min",
        # label="left",
        # closed="left",
        # origin="start_day",
        # offset="18h"
    ).agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })

    return df.dropna()

def resample_to_30m_old(df):

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


# daily_candles = []

# for ts, row in df_1d.iterrows():
#     daily_candles.append({
#         "timestamp": ts.isoformat(),
#         "open": row["Open"],
#         "high": row["High"],
#         "low": row["Low"],
#         "close": row["Close"],
#         "volume": row["Volume"]
#     })


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


