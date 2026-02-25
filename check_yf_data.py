import yfinance as yf
import pandas as pd
from datetime import datetime

TICKER = "NQ=F"  # Nasdaq futures
INTERVALS = ["3m", "30m"]

results = []

for interval in INTERVALS:

    print(f"\nDownloading {interval} data...")

    df = yf.download(
        TICKER,
        period="max",
        interval=interval,
        progress=False
    )

    if df.empty:
        print(f"No data returned for {interval}")
        continue

    df = df.dropna()

    start_date = df.index.min()
    end_date = df.index.max()

    months_span = (end_date - start_date).days / 30

    print(f"Interval: {interval}")
    print(f"Start: {start_date}")
    print(f"End:   {end_date}")
    print(f"Approx Months Available: {round(months_span,2)}")
    print(f"Total Bars: {len(df)}")

    # Save to CSV for inspection
    filename = f"nq_{interval}_data.csv"
    df.to_csv(filename)
    print(f"Saved to {filename}")

    results.append({
        "interval": interval,
        "start": start_date,
        "end": end_date,
        "months_span": months_span,
        "bars": len(df)
    })

print("\nSummary:")
print(pd.DataFrame(results))