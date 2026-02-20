# def insert_trade(candidate):

#     entry = candidate.entry_imbalance["entry"]
#     side = candidate.side
#     sweep = candidate.sweep_candle

#     if side == "buy_side":
#         stop = sweep["high"]
#         risk = stop - entry
#         tp = entry - (risk * 1.5)
#         trade_side = "short"
#     else:
#         stop = sweep["low"]
#         risk = entry - stop
#         tp = entry + (risk * 1.5)
#         trade_side = "long"

#     trade_id = f"{candidate.instrument}_{candidate.sweep_timestamp}"

#     conn = sqlite3.connect(DB_FILE)
#     cursor = conn.cursor()

#     cursor.execute("""
#     INSERT OR IGNORE INTO trades
#     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#     """, (
#         trade_id,
#         candidate.sweep_timestamp,
#         candidate.instrument,
#         trade_side,
#         entry,
#         stop,
#         tp,
#         risk,
#         candidate.entry_imbalance["type"],
#         "OPEN",
#         None
#     ))

#     conn.commit()
#     conn.close()

# def update_trade_result(trade_id, outcome):

#     conn = sqlite3.connect(DB_FILE)
#     cursor = conn.cursor()

#     if outcome == "TP":
#         cursor.execute("""
#             UPDATE trades
#             SET status = 'WIN',
#                 r_multiple = 1.5
#             WHERE trade_id = ?
#         """, (trade_id,))

#     elif outcome == "SL":
#         cursor.execute("""
#             UPDATE trades
#             SET status = 'LOSS',
#                 r_multiple = -1.0
#             WHERE trade_id = ?
#         """, (trade_id,))

#     conn.commit()
#     conn.close()

# def calculate_performance():

#     conn = sqlite3.connect(DB_FILE)
#     cursor = conn.cursor()

#     cursor.execute("""
#         SELECT COUNT(*),
#                SUM(CASE WHEN status='WIN' THEN 1 ELSE 0 END),
#                SUM(CASE WHEN status='LOSS' THEN 1 ELSE 0 END),
#                SUM(r_multiple)
#         FROM trades
#         WHERE status IN ('WIN','LOSS')
#     """)

#     result = cursor.fetchone()
#     conn.close()

#     total_trades, wins, losses, total_r = result

#     if total_trades == 0:
#         return "No closed trades yet."

#     win_rate = (wins / total_trades) * 100
#     expectancy = total_r / total_trades

#     return f"""
# Performance Summary

# Total Trades: {total_trades}
# Wins: {wins}
# Losses: {losses}
# Win Rate: {round(win_rate,2)}%

# Total R: {round(total_r,2)}
# Expectancy (R per trade): {round(expectancy,2)}
# """