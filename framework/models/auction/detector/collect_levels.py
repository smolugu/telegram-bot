def collect_levels(
    daily_swings,
    daily_fvgs,
    daily_vis,

    h7_swings,
    h7_fvgs,
    h7_vis,

    h4_swings,
    h4_fvgs,
    h4_vis,
):
    levels = []

    levels.extend(daily_swings)
    levels.extend(daily_fvgs)
    levels.extend(daily_vis)

    levels.extend(h7_swings)
    levels.extend(h7_fvgs)
    levels.extend(h7_vis)

    levels.extend(h4_swings)
    levels.extend(h4_fvgs)
    levels.extend(h4_vis)

    return levels