from datetime import datetime
from zoneinfo import ZoneInfo


class WeeklyContext:

    def __init__(self, tz_str="America/New_York"):

        self.tz = ZoneInfo(tz_str)

        # Weekly levels
        self.weekly_high = None
        self.weekly_low = None

        # Day tracking
        self.high_day = None
        self.low_day = None

        # State
        self.days_data = {}  # {day: {"high": x, "low": x}}

        # Signals
        self.cisd = None
        self.fvg = None

        # Profile
        self.profile = None

    # ----------------------------------
    # Update with each candle
    # ----------------------------------
    def update(self, candle):

        dt = datetime.fromisoformat(candle["timestamp"]).astimezone(self.tz)
        day = dt.strftime("%A")

        high = candle["high"]
        low = candle["low"]

        # -------------------------
        # Store daily data
        # -------------------------
        if day not in self.days_data:
            self.days_data[day] = {"high": high, "low": low}
        else:
            self.days_data[day]["high"] = max(self.days_data[day]["high"], high)
            self.days_data[day]["low"] = min(self.days_data[day]["low"], low)

        # -------------------------
        # Weekly High / Low Tracking
        # -------------------------
        if self.weekly_high is None or high > self.weekly_high:
            self.weekly_high = high
            self.high_day = day

        if self.weekly_low is None or low < self.weekly_low:
            self.weekly_low = low
            self.low_day = day

    # ----------------------------------
    # Detect CISD (1H)
    # ----------------------------------
    def update_cisd(self, prev_candle, current_candle):

        # Bullish CISD
        if current_candle["close"] > prev_candle["high"]:
            self.cisd = "bullish"

        # Bearish CISD
        elif current_candle["close"] < prev_candle["low"]:
            self.cisd = "bearish"

    # ----------------------------------
    # Detect FVG (1H)
    # ----------------------------------
    def update_fvg(self, c1, c2, c3):

        # Bullish FVG
        if c1["high"] < c3["low"]:
            self.fvg = {
                "type": "bullish",
                "low": c1["high"],
                "high": c3["low"]
            }

        # Bearish FVG
        elif c1["low"] > c3["high"]:
            self.fvg = {
                "type": "bearish",
                "low": c3["high"],
                "high": c1["low"]
            }

    # ----------------------------------
    # Infer Weekly Profile
    # ----------------------------------
    def infer_profile(self):

        # -------------------------
        # Classic Expansion Week
        # -------------------------
        if self.low_day in ["Monday", "Tuesday"] or self.high_day in ["Monday", "Tuesday"]:
            self.profile = "classic_expansion"

        # -------------------------
        # Midweek Reversal
        # -------------------------
        if self.low_day == "Wednesday" or self.high_day == "Wednesday":
            self.profile = "midweek_reversal"

        # -------------------------
        # Weekly Judas
        # -------------------------
        if self.cisd and self.fvg:
            if self.low_day in ["Monday", "Tuesday"] or self.high_day in ["Monday", "Tuesday"]:
                self.profile = "weekly_judas"

        # -------------------------
        # Consolidation Reversal
        # -------------------------
        if (
            "Monday" in self.days_data
            and "Tuesday" in self.days_data
            and "Wednesday" in self.days_data
        ):
            m = self.days_data["Monday"]
            t = self.days_data["Tuesday"]
            w = self.days_data["Wednesday"]

            range_mt = max(m["high"], t["high"], w["high"]) - min(m["low"], t["low"], w["low"])

            if range_mt < 0.5 * (self.weekly_high - self.weekly_low):
                self.profile = "consolidation_reversal"

        return self.profile

    # ----------------------------------
    # Bias for upcoming sessions
    # ----------------------------------
    def get_bias(self):

        if self.profile == "classic_expansion":
            return "continue_trend"

        if self.profile == "midweek_reversal":
            return "reverse_then_expand"

        if self.profile == "weekly_judas":
            return "trap_then_expand"

        if self.profile == "consolidation_reversal":
            return "breakout_pending"

        return "neutral"