
from data.models.candle import Candle
from framework.models.auction.models.htf_cisd import HTFCISD

def detect_htf_cisd(
    candles: list[Candle],
    timeframe: str,
    ) -> list[HTFCISD]:

    if len(candles) < 3:
            return []
    
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
                    timestamp=curr.timestamp,
                    upper=last_bearish.open,
                    lower=min(last_bearish.close, curr.open),
                    upper_wick=last_bearish.high,
                    lower_wick=last_bearish.low,
                    price=last_bearish.open,
                    is_bullish=True,
                    is_buy_side=False,
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
                    timestamp=curr.timestamp,
                    upper=max(last_bullish.close,curr.open),
                    lower=last_bullish.open,
                    upper_wick=last_bullish.high,
                    lower_wick=last_bullish.low,
                    price=last_bullish.open,
                    is_bullish=False,
                    is_buy_side=True
                )
            )
            last_bullish = None

        # Update the reference candles AFTER checking for CISD.
        if curr.close > curr.open:
            last_bullish = curr
        elif curr.close < curr.open:
            last_bearish = curr

    return cisds


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
                    timestamp=curr.timestamp,
                    upper=last_bearish.open,
                    lower=min(last_bearish.close, curr.open),
                    upper_wick=last_bearish.high,
                    lower_wick=last_bearish.low,
                    price=last_bearish.open,
                    is_bullish=True,
                    is_buy_side=False
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
                    timestamp=curr.timestamp,
                    upper=max(last_bullish.close,curr.open),
                    lower=last_bullish.open,
                    upper_wick=last_bullish.high,
                    lower_wick=last_bullish.low,
                    price=last_bullish.open,
                    is_bullish=False,
                    is_buy_side=True
                )
            )
            last_bullish = None

        # Update the reference candles AFTER checking for CISD.
        if curr.close > curr.open:
            last_bullish = curr
        elif curr.close < curr.open:
            last_bearish = curr

    return cisds

