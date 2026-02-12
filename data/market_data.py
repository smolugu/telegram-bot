import yfinance as yf


def fetch_symbol_data(symbol: str):

    ticker = yf.Ticker(symbol)

    return {
        "30m": _format(ticker.history(interval="30m", period="7d")),
        "1h": _format(ticker.history(interval="60m", period="14d")),
        "3m": _format(ticker.history(interval="3m", period="2d")),
        "protected_high": None,  # Fill from swing logic
        "protected_low": None
    }


def fetch_market_data():

    nq = fetch_symbol_data("NQ=F")
    es = fetch_symbol_data("ES=F")

    return {
        "NQ": nq,
        "ES": es,
        "daily": _format(yf.Ticker("NQ=F").history(interval="1d", period="10d")),
        "current_price": nq["30m"][-1]["close"]
    }


def _format(df):
    df = df.reset_index()
    return [
        {
            "timestamp": row["Datetime"].isoformat(),
            "open": row["Open"],
            "high": row["High"],
            "low": row["Low"],
            "close": row["Close"]
        }
        for _, row in df.iterrows()
    ]
