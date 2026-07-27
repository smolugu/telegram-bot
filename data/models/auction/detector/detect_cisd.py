
from data.datamodels.candle import Candle
from data.models.auction.models.htf_cisd import HTFCISD

def detect_cisd(
    candles: list[Candle],
    timeframe: str,
    ) -> list[HTFCISD]:

    cisds = []

    last_bullish: Candle | None = None
    last_bearish: Candle | None = None

    for curr in candles:

        # Bullish CISD:
        # Close above the high of the last bearish candle.
        if (
            last_bearish is not None
            and curr.close > last_bearish.open
        ):
            cisds.append(
                HTFCISD(
                    timeframe=timeframe,
                    timestamp=curr.time,
                    upper_body=last_bearish.open,
                    lower_body=min(last_bearish.close, curr.open),
                    upper_wick=last_bearish.high,
                    lower_wick=last_bearish.low,
                    bullish=True,
                )
            )
            last_bearish = None

        # Bearish CISD:
        # Close below the low of the last bullish candle.
        elif (
            last_bullish is not None
            and curr.close < last_bullish.open
        ):
            cisds.append(
                HTFCISD(
                    timeframe=timeframe,
                    timestamp=curr.time,
                    upper_body=max(last_bullish.close,curr.open),
                    lower_body=last_bullish.open,
                    upper_wick=last_bullish.high,
                    lower_wick=last_bullish.low,
                    bullish=False,
                )
            )
            last_bullish = None

        # Update the reference candles AFTER checking for CISD.
        if curr.close > curr.open:
            last_bullish = curr
        elif curr.close < curr.open:
            last_bearish = curr

    return cisds

# def find_last_opposite_candle(candles: list[Candle], index: int, bullish: bool) -> Candle | None:
#     """
#     For bullish=True:
#         Returns the last bearish candle before index.

#     For bullish=False:
#         Returns the last bullish candle before index.
#     """
#     for i in range(index - 1, -1, -1):
#         candle = candles[i]

#         if bullish:
#             if candle.close < candle.open:
#                 return candle
#         else:
#             if candle.close > candle.open:
#                 return candle

#     return None


# def detect_cisd(
#     candles: list[Candle],
#     timeframe: str,
#     ) -> list[HTFCISD]:

#     cisds = []
#     last_bearish = find_last_opposite_candle(candles, i, bullish=True)
    

#     for i in range(1, len(candles)):

#         prev = candles[i - 1]
#         curr = candles[i]

#         # Bullish CISD
#         if curr.close > prev.high:

#             cisds.append(
#                 HTFCISD(
#                     timeframe=timeframe,
#                     timestamp=curr.time,
#                     price=prev.high,
#                     bullish=True,
#                 )
#             )

#         # Bearish CISD
#         elif curr.close < prev.low:

#             cisds.append(
#                 HTFCISD(
#                     timeframe=timeframe,
#                     timestamp=curr.time,
#                     price=prev.low,
#                     bullish=False,
#                 )
#             )

#     return cisds