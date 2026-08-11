from framework.models.auction.models.auction_context import AuctionContext
from framework.models.auction.models.base_model import HTFCisdStatus, HTFFvgStatus, HTFSwingStatus, HTFViStatus
from framework.models.auction.models.htf_cisd import HTFCISD
from framework.models.auction.models.htf_fvg import HTFFVG
from framework.models.auction.models.htf_swing import HTFSwing
from framework.models.auction.models.htf_vi import HTFVolumeImbalance


def build_auction_context(levels):

    context = AuctionContext()

    for level in levels:
        #
        # Swing
        #
        if isinstance(level, HTFSwing):
            if level.swing_type == "BUY_SIDE":
                context.bullish_swings.append(level)
                context.bullish_levels.append(level)
            else:
                context.bearish_swings.append(level)
                context.bearish_levels.append(level)
                
        #
        # FVG
        #
        elif isinstance(level, HTFFVG):
            if level.is_bullish:
                context.bullish_fvgs.append(level)
                context.bullish_levels.append(level)
            else:
                context.bearish_fvgs.append(level)
                context.bearish_levels.append(level)

        #
        # VI
        #
        elif isinstance(level, HTFVolumeImbalance):
            if level.is_bullish:
                context.bullish_vis.append(level)
                context.bullish_levels.append(level)
            else:
                context.bearish_vis.append(level)
                context.bearish_levels.append(level)

        #
        # CISD
        #
        elif isinstance(level, HTFCISD):
            if level.is_bullish:
                context.bullish_cisds.append(level)
                context.bullish_levels.append(level)
            else:
                context.bearish_cisds.append(level)
                context.bearish_levels.append(level)

    open_bullish_levels = []
    open_bearish_levels = []
    # populate nearest open levels - swings
    open_bullish_swings = [
        s for s in context.bullish_swings
        if s.status == HTFSwingStatus.OPEN
    ]
    open_bullish_levels = open_bullish_levels + open_bullish_swings

    if open_bullish_swings:
        context.nearest_bullish_swing = open_bullish_swings[0]

    open_bearish_swings = [
        s for s in context.bearish_swings
        if s.status == HTFSwingStatus.OPEN
    ]
    open_bearish_levels = open_bearish_levels + open_bearish_swings

    if open_bearish_swings:
        context.nearest_bearish_swing = open_bearish_swings[0]

    # populate nearest open levels - fvgs
    open_bullish_fvgs = [
        s for s in context.bullish_fvgs
        if s.status == HTFFvgStatus.OPEN
    ]
    open_bullish_levels = open_bullish_levels + open_bullish_fvgs

    if open_bullish_fvgs:
        context.nearest_bullish_fvg = open_bullish_fvgs[0]

    open_bearish_fvgs = [
        s for s in context.bearish_fvgs
        if s.status == HTFFvgStatus.OPEN
    ]
    open_bearish_levels = open_bearish_levels + open_bearish_fvgs

    if open_bearish_fvgs:
        context.nearest_bearish_fvg = open_bearish_fvgs[0]

    # populate nearest open levels - vis
    open_bullish_vis = [
        s for s in context.bullish_vis
        if s.status == HTFViStatus.OPEN
    ]
    open_bullish_levels = open_bullish_levels + open_bullish_vis

    if open_bullish_vis:
        context.nearest_bullish_vi = open_bullish_vis[0]

    open_bearish_vis = [
        s for s in context.bearish_vis
        if s.status == HTFViStatus.OPEN
    ]
    open_bearish_levels = open_bearish_levels + open_bearish_vis

    if open_bearish_vis:
        context.nearest_bearish_vi = open_bearish_vis[0]

    # populate nearest open levels - cisds
    open_bullish_cisds = [
        s for s in context.bullish_cisds
        if s.status == HTFCisdStatus.OPEN
    ]
    open_bullish_levels = open_bullish_levels + open_bullish_cisds

    if open_bullish_cisds:
        context.nearest_bullish_cisd = open_bullish_cisds[0]

    open_bearish_cisds = [
        s for s in context.bearish_cisds
        if s.status == HTFCisdStatus.OPEN
    ]
    open_bearish_levels = open_bearish_levels + open_bearish_cisds

    if open_bearish_cisds:
        context.nearest_bearish_cisd = open_bearish_cisds[0]

    open_bullish_levels.sort(
        key=lambda x: x.price
    )
    open_bearish_levels.sort(
        key=lambda x: x.price,
        reverse=True
    )
    context.nearest_bullish_level = open_bullish_levels[0]
    context.nearest_bearish_level = open_bearish_levels[0]

    return context