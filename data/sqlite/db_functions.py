import datetime
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "tradeoncall.db")
print("Database file path functions.py:", DB_FILE)


def insert_trade(candidate):

    entry = candidate.fvg_data["entry"]
    side = candidate.side
    stop = candidate.sweep_candle_extreme

    if side == "buy_side":
        stop = stop
        risk = stop - entry
        tp = entry - (risk * 1.5)
        trade_side = "short"
    else:
        stop = candidate.sweep_candle_extreme
        risk = entry - stop
        tp = entry + (risk * 1.5)
        trade_side = "long"

    trade_id = f"{candidate.fvg_data['instrument']}_{candidate.sweep_timestamp}"

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO trades
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
    """, (
        trade_id,
        candidate.sweep_timestamp,
        candidate.fvg_data["instrument"],
        trade_side,
        entry,
        stop,
        tp,
        risk,
        candidate.fvg_data["type"],
        "OPEN",
        None
    ))

    conn.commit()
    conn.close()

def update_trade_result(trade_id, outcome):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    

    if outcome == "TP":
        cursor.execute("""
            UPDATE trades
            SET status = 'WIN',
                r_multiple = 1.5
            WHERE trade_id = ?
        """, (trade_id,))

    elif outcome == "SL":
        cursor.execute("""
            UPDATE trades
            SET status = 'LOSS',
                r_multiple = -1.0
            WHERE trade_id = ?
        """, (trade_id,))

    conn.commit()
    conn.close()

def calculate_performance():

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*),
               SUM(CASE WHEN status='WIN' THEN 1 ELSE 0 END),
               SUM(CASE WHEN status='LOSS' THEN 1 ELSE 0 END),
               SUM(r_multiple)
        FROM trades
        WHERE status IN ('WIN','LOSS')
    """)

    result = cursor.fetchone()
    conn.close()

    total_trades, wins, losses, total_r = result

    if total_trades == 0:
        return "No closed trades yet."

    win_rate = (wins / total_trades) * 100
    expectancy = total_r / total_trades

    return f"""
Performance Summary

Total Trades: {total_trades}
Wins: {wins}
Losses: {losses}
Win Rate: {round(win_rate,2)}%

Total R: {round(total_r,2)}
Expectancy (R per trade): {round(expectancy,2)}
"""



def check_trade_hit(trade, candle):

    trade_id, side, entry, stop, tp = trade

    high = candle["high"]
    low = candle["low"]

    # --------------------------------
    # SHORT TRADE
    # --------------------------------
    if side == "short":

        # SL first rule if both touched
        if high >= stop and low <= tp:
            return trade_id, "SL"

        if high >= stop:
            return trade_id, "SL"

        if low <= tp:
            return trade_id, "TP"

    # --------------------------------
    # LONG TRADE
    # --------------------------------
    elif side == "long":

        if low <= stop and high >= tp:
            return trade_id, "SL"

        if low <= stop:
            return trade_id, "SL"

        if high >= tp:
            return trade_id, "TP"

    return None, None


def get_open_trades():

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT trade_id, side, entry, stop, tp
        FROM trades
        WHERE status = 'OPEN'
    """)

    trades = cursor.fetchall()
    conn.close()

    return trades


def monitor_open_trades(new_candle):

    open_trades = get_open_trades()

    for trade in open_trades:

        trade_id, outcome = check_trade_hit(trade, new_candle)

        if outcome:
            update_trade_result(trade_id, outcome)
            print(f"Trade {trade_id} closed as {outcome}")