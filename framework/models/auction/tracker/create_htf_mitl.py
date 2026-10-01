from datetime import datetime

from framework.models.auction.models.enums import SwingType
from framework.models.auction.models.htf_mitl import HTFMITL
from framework.models.auction.models.htf_swing import HTFSwing


def _create_htf_mitl_from_swing(
    swing: HTFSwing,
    confirmation_time: datetime,
) -> HTFMITL:

    return HTFMITL(
        timeframe=swing.timeframe,
        timestamp=swing.timestamp,
        confirmation_time=confirmation_time,
        price=swing.price,
        is_bullish=swing.is_bullish,
        is_buy_side=(
            swing.swing_type == SwingType.SELL_SIDE
        ),
    )