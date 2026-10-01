from data.models.candle import Candle
from framework.models.auction.models.enums import HTFMitlStatus
from framework.models.auction.models.htf_mitl import HTFMITL


def update_mitl_status(
    mitls: list[HTFMITL],
    candles: list[Candle],
    htf_candles: list[Candle],
) -> None:

    if not mitls:
        return

    candles = sorted(candles, key=lambda c: c.timestamp)
    htf_candles = sorted(htf_candles, key=lambda c: c.timestamp)

    for mitl in mitls:

        if mitl.status == HTFMitlStatus.RECLAIMED:
            continue

        # -----------------------------------------------------
        # LTF interaction / sweep
        # -----------------------------------------------------
        for candle in candles:

            if candle.timestamp <= mitl.confirmation_time:
                continue

            if mitl.is_buy_side:
                # Buy-side MITL:
                # price approaches from below.
                if candle.high >= mitl.price:
                    mitl.is_swept = True
                    mitl.is_mitigated = True
                    mitl.status = HTFMitlStatus.SWEPT
                    mitl.mitigation_time = candle.timestamp
                    break

            else:
                # Sell-side MITL:
                # price approaches from above.
                if candle.low <= mitl.price:
                    mitl.is_swept = True
                    mitl.is_mitigated = True
                    mitl.status = HTFMitlStatus.SWEPT
                    mitl.mitigation_time = candle.timestamp
                    break
        
        # -----------------------------------------------------
        # HTF invalidation / reclaim
        # -----------------------------------------------------
        for htf_candle in htf_candles:

            if htf_candle.timestamp <= mitl.confirmation_time:
                continue

            if mitl.is_buy_side:
                # Buy-side MITL is ABOVE price.
                # HTF close above it = invalidated/reclaimed.
                if htf_candle.close > mitl.price:
                    mitl.status = HTFMitlStatus.RECLAIMED
                    break

            else:
                # Sell-side MITL is BELOW price.
                # HTF close below it = invalidated/reclaimed.
                if htf_candle.close < mitl.price:
                    mitl.status = HTFMitlStatus.RECLAIMED
                    break
