# Liquidity sweep (0-25)
def score_liquidity(sweep_level):
    if sweep_level in ["PDH", "PDL"]:
        return 25
    elif sweep_level in ["ASIA_HIGH", "ASIA_LOW"]:
        return 20
    elif sweep_level == "IB":
        return 10
    return 0

# day type alignment (0-20)
def score_day_type(day_type, setup_type):
    if day_type == "reversal" and setup_type == "reversal":
        return 20
    elif day_type == "range":
        return 15
    elif day_type == "trend" and setup_type == "reversal":
        return 0
    return 5

# session timing (0-20)
def score_session(hour):

    # NY AM (9:30–11:30)
    if 9 <= hour < 11:
        return 5   # avoid reversals

    # NY Lunch (11:30–13:30) ⭐ BEST
    if 11 <= hour < 13:
        return 20

    # NY PM (13:30–16:00)
    if 13 <= hour < 16:
        return 15

    return 0

# execution quality (0-20)
def score_execution(ob_formed, tapped_imbalance, clean_structure):

    score = 0

    if ob_formed:
        score += 8

    if tapped_imbalance:
        score += 8

    if clean_structure:
        score += 4

    return score

#  expansion context (0-15)
def score_expansion(expansion_ratio, expansion_speed):

    score = 0

    # Exhaustion = good for reversal
    if expansion_ratio > 1.2:
        score += 10

    if expansion_speed < 0.5:
        score += 5

    return score

# final scoring function
def compute_base_trade_score(context):

    score = 0

    score += score_liquidity(context["sweep_level"])
    score += score_day_type(context["day_type"], context["setup_type"])
    score += score_session(context["hour"])
    score += score_execution(
        context["ob_formed"],
        context["tapped_imbalance"],
        context["clean_structure"]
    )
    score += score_expansion(
        context["expansion_ratio"],
        context["expansion_speed"]
    )

    return score

#  trade decision layer
def should_take_trade(score):

    if score >= 80:
        return "A+ setup"
    elif score >= 70:
        return "A setup"
    elif score >= 60:
        return "B setup (optional)"
    else:
        return "skip"
    

# score based on ICT timing - 90m cycles
def score_ict_time(hour, minute):

    time_tuple = (hour, minute)

    score_map = {

        # Asia / Globex
        (19,30): 8,
        (21,0): 8,
        (22,30): 7,
        (0,0): 6,

        # London build
        (1,30): 10,
        (3,0): 12,
        (4,30): 12,
        (6,0): 13,
        (7,30): 14,

        # NY AM
        (9,0): 16,
        (10,30): 20,

        # NY Lunch ⭐
        (12,0): 25,
        (13,30): 22,

        # NY PM
        (15,0): 12,
    }

    return score_map.get(time_tuple, 0)

# ICT time score - add day type multiplier
def adjust_for_day_type(score, day_type):

    if day_type == "reversal":
        return score * 1.2

    if day_type == "trend":
        return score * 0.6  # penalize reversals

    return score

# ICT timing score - add session boost
def adjust_for_session(score, hour):

    # Lunch boost
    if 12 <= hour < 14:
        return score + 5

    # AM penalty for reversals
    if 9 <= hour < 11:
        return score - 5

    return score

# Final ICT time score
def compute_ict_time_score(hour, minute, day_type):

    base = score_ict_time(hour, minute)

    adjusted = adjust_for_day_type(base, day_type)
    adjusted = adjust_for_session(adjusted, hour)

    return max(0, round(adjusted))


# Final score after adding ICT score multiplier
def final_trade_score(base_trade_score, ict_time_score):
    final_score = base_trade_score * (1 + ict_time_score / 100)
    return final_score

def final_trade_filter(base_score, final_score, atr_usage, is_reversal, is_continuation):
    take_trade = False
    if final_score >= 85:
        take_trade = True
    else:
        take_trade = False
    if base_score < 60:
        take_trade = False
    
    # final atr filter for reversal and continuation setups
    if atr_usage < 0.4 and is_reversal:
        take_trade = False
    if atr_usage > 0.9 and is_continuation:
        take_trade = False

    return take_trade

# ATR bias
def compute_atr_bias(session_range, daily_atr):

    if daily_atr is None or daily_atr == 0:
        return "neutral", 0

    atr_usage = session_range / daily_atr

    if atr_usage >= 1.0:
        return "reversal", 20

    elif atr_usage >= 0.7:
        return "reversal", 10

    elif atr_usage <= 0.4:
        return "continuation", 15

    else:
        return "neutral", 5
# Next level enhancements

# Relative expansion
# if context["relative_expansion"] < 0:
#     score += 5  # divergence = reversal edge

#  Distance from IB
# if context["distance_from_ib"] > threshold:
#     score += 5

#  Killzone boost
# if 12 <= hour <= 13:
#     score += 5