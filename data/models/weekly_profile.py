from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


class WeeklyContext:

    def __init__(
        self,
        instrument,
        daily_candles,
        candles_1h,
        current_date,
        tz_str="America/New_York"
    ):

        self.tz = ZoneInfo(tz_str)

        # -----------------------------------------
        # Input Data
        # -----------------------------------------
        self.instrument = instrument
        self.daily_candles = daily_candles
        self.candles_1h = candles_1h

        self.current_date = (
            datetime.fromisoformat(current_date)
            .astimezone(self.tz)
            .date()
        )

        # -----------------------------------------
        # Weekly Levels
        # -----------------------------------------
        self.weekly_high = None
        self.weekly_low = None

        self.high_day = None
        self.low_day = None

        # -----------------------------------------
        # Day Tracking
        # -----------------------------------------
        self.days_data = {}

        # -----------------------------------------
        # Weekly Signals
        # -----------------------------------------
        self.cisd = None
        self.fvg = None

        # -----------------------------------------
        # Weekly State
        # -----------------------------------------
        self.profile = None
        self.bias = "neutral"

        # -----------------------------------------
        # Internal
        # -----------------------------------------
        self.processed_days = []

        # -----------------------------------------
        # Initialize
        # -----------------------------------------
        self._build_context()

    # =====================================================
    # BUILD CONTEXT USING PREVIOUS DAYS OF CURRENT WEEK
    # =====================================================
    def _build_context(self):

        week_start = self.current_date - timedelta(
            days=self.current_date.weekday()
        )

        # -------------------------------------------------
        # PROCESS DAILY CANDLES
        # -------------------------------------------------
        for candle in self.daily_candles:

            dt = (
                datetime.fromisoformat(candle["timestamp"])
                .astimezone(self.tz)
            )

            candle_date = dt.date()

            # Only process previous days
            if (
                candle_date >= week_start
                and candle_date < self.current_date
            ):

                self._update_daily(candle)

        # -------------------------------------------------
        # PROCESS 1H CANDLES
        # -------------------------------------------------
        self._process_1h()

        # -------------------------------------------------
        # FINAL PROFILE
        # -------------------------------------------------
        self.infer_profile()

    # =====================================================
    # UPDATE DAILY STRUCTURE
    # =====================================================
    def _update_daily(self, candle):

        dt = (
            datetime.fromisoformat(candle["timestamp"])
            .astimezone(self.tz)
        )

        day = dt.strftime("%A")

        high = candle["high"]
        low = candle["low"]

        self.days_data[day] = {
            "high": high,
            "low": low,
            "close": candle["close"],
            "open": candle["open"]
        }

        self.processed_days.append(day)

        # -------------------------------------------------
        # WEEKLY HIGH
        # -------------------------------------------------
        if (
            self.weekly_high is None
            or high > self.weekly_high
        ):
            self.weekly_high = high
            self.high_day = day

        # -------------------------------------------------
        # WEEKLY LOW
        # -------------------------------------------------
        if (
            self.weekly_low is None
            or low < self.weekly_low
        ):
            self.weekly_low = low
            self.low_day = day

    # =====================================================
    # PROCESS 1H STRUCTURE
    # =====================================================
    def _process_1h(self):

        week_start = self.current_date - timedelta(
            days=self.current_date.weekday()
        )

        filtered = []

        for c in self.candles_1h:

            dt = (
                datetime.fromisoformat(c["timestamp"])
                .astimezone(self.tz)
            )

            candle_date = dt.date()

            if (
                candle_date >= week_start
                and candle_date < self.current_date
            ):
                filtered.append(c)

        # -------------------------------------------------
        # SORT
        # -------------------------------------------------
        filtered.sort(
            key=lambda x: x["timestamp"]
        )

        # -------------------------------------------------
        # PROCESS CISD
        # -------------------------------------------------
        for i in range(1, len(filtered)):

            prev_candle = filtered[i - 1]
            current_candle = filtered[i]

            self.update_cisd(
                prev_candle,
                current_candle
            )

        # -------------------------------------------------
        # PROCESS FVG
        # -------------------------------------------------
        for i in range(2, len(filtered)):

            c1 = filtered[i - 2]
            c2 = filtered[i - 1]
            c3 = filtered[i]

            self.update_fvg(c1, c2, c3)

    # =====================================================
    # CISD
    # =====================================================
    def update_cisd(
        self,
        prev_candle,
        current_candle
    ):

        if (
            current_candle["close"]
            > prev_candle["high"]
        ):
            self.cisd = "bullish"

        elif (
            current_candle["close"]
            < prev_candle["low"]
        ):
            self.cisd = "bearish"

    # =====================================================
    # FVG
    # =====================================================
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

    # =====================================================
    # INFER PROFILE
    # =====================================================
    def infer_profile(self):

        # -------------------------------------------------
        # MONDAY/TUESDAY EXTREME
        # -------------------------------------------------
        if (
            self.low_day in ["Monday", "Tuesday"]
            or self.high_day in ["Monday", "Tuesday"]
        ):

            self.profile = "classic_expansion"

        # -------------------------------------------------
        # MIDWEEK REVERSAL
        # -------------------------------------------------
        if (
            self.low_day == "Wednesday"
            or self.high_day == "Wednesday"
        ):

            self.profile = "midweek_reversal"

        # -------------------------------------------------
        # WEEKLY JUDAS
        # -------------------------------------------------
        if self.cisd and self.fvg:

            if (
                self.low_day in ["Monday", "Tuesday"]
                or self.high_day in ["Monday", "Tuesday"]
            ):

                self.profile = "weekly_judas"

        # -------------------------------------------------
        # CONSOLIDATION PROFILE
        # -------------------------------------------------
        if (
            "Monday" in self.days_data
            and "Tuesday" in self.days_data
        ):

            monday = self.days_data["Monday"]
            tuesday = self.days_data["Tuesday"]

            combined_high = max(
                monday["high"],
                tuesday["high"]
            )

            combined_low = min(
                monday["low"],
                tuesday["low"]
            )

            combined_range = (
                combined_high - combined_low
            )

            weekly_range = (
                self.weekly_high - self.weekly_low
                if self.weekly_high
                and self.weekly_low
                else 0
            )

            if (
                weekly_range > 0
                and combined_range < 0.5 * weekly_range
            ):

                self.profile = "consolidation_reversal"

        # -------------------------------------------------
        # DEFAULT
        # -------------------------------------------------
        if self.profile is None:
            self.profile = "developing"

        self.bias = self.get_bias()

        return self.profile

    # =====================================================
    # GET BIAS
    # =====================================================
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

    # =====================================================
    # SUMMARY
    # =====================================================
    def summary(self):

        return {
            "profile": self.profile,
            "bias": self.bias,
            "weekly_high": self.weekly_high,
            "weekly_low": self.weekly_low,
            "high_day": self.high_day,
            "low_day": self.low_day,
            "cisd": self.cisd,
            "fvg": self.fvg,
            "processed_days": self.processed_days
        }

class WeeklyContextReal:

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

# call in main file to update weekly profile
# weekly_context.update(candle_1h)
# weekly_context.update_cisd(prev, current)
# weekly_context.update_fvg(c1, c2, c3)

# profile = weekly_context.infer_profile()
