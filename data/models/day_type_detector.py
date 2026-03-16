# Three Main Day Types
# 1. Trend Day
#  - IB breaks early
#  - Price stays outside IB
#  - range expands steadily
#  - Favor continuation, avoid reversals

# 2. Reversal Day
#  - London Sweep
#  - Ny reverses direction
#  - Closes inside IB after sweep
#  - Ob forms inside IB

# 3. Range Day
#  - IB not broken
#  - Price oscillates inside range
#  - ATR expansion low
#  - small targets, avoid breakouts

# Inputs needed: IB_high, IB_low, Ny_am bias, daily ATR, current range
from datetime import datetime

class DayTypeContext:

    def __init__(self, instrument, atr):

        self.instrument = instrument
        self.daily_atr = atr
        self.day_type = None
        self.bias = "neutral"

        self.ib_high = None
        self.ib_low = None
        self.ib_ce = None

        self.daily_atr = None


    def update(self, candle, day_high, day_low, daily_atr):

        ts = datetime.fromisoformat(candle["timestamp"])

        close = candle["close"]

        hour = ts.hour
        minute = ts.minute

        range_today = day_high - day_low


        # detect trend day
        if hour == 10 and minute == 30:
            print("instrument: ", self.instrument)
            print("self.ib_high: ", self.ib_high)

            if close > self.ib_high or close < self.ib_low:

                if range_today > daily_atr * 0.5:
                    self.day_type = "trend"
                    if close > self.ib_high:
                        self.bias = "bullish"
                    elif close < self.ib_low:
                        self.bias = "bearish"
                        
                else:
                    print("No trend 10:30: ", range_today, daily_atr)
            
            


        # detect range day
        if hour == 11 and minute == 30:

            if self.ib_low <= close <= self.ib_high:
                self.day_type = "range"
            else:
                print("Not a range day: ", self.ib_low, close, self.ib_high)


        # fallback
        if self.day_type is None and hour >= 12:
            print("inside fallback hour >12")
            self.day_type = "normal"
        else:
            print("no fall back")



class IBDayTypeContext:

    def __init__(self, instrument):

        self.instrument = instrument

        self.ib_high = None
        self.ib_low = None
        self.ib_range = None
        self.ib_ce = None

        self.session_high = None
        self.session_low = None

        self.daily_atr = None
        self.session_range = None
        self.atr_expansion_ratio = None


        self.day_type = None
        self.finalized = False

        self.expansion_ratio = 0
        self.expansion_speed = 0
        self.relative_expansion = 0


    def set_ib(self, ib_high, ib_low):

        self.ib_high = ib_high
        self.ib_low = ib_low
        self.ib_range = ib_high - ib_low
        self.ib_ce = (ib_high + ib_low) / 2


    def update_session_range(self, high, low):

        if self.session_high is None:
            self.session_high = high
            self.session_low = low
        else:
            self.session_high = max(self.session_high, high)
            self.session_low = min(self.session_low, low)


    def compute_expansion_metrics(
        self,
        timestamp,
        nq_ratio=None,
        es_ratio=None
    ):

        ts = datetime.fromisoformat(timestamp)

        bullish = max(0, self.session_high - self.ib_high)
        bearish = max(0, self.ib_low - self.session_low)

        expansion = max(bullish, bearish)

        if self.ib_range > 0:
            self.expansion_ratio = expansion / self.ib_range

        minutes_since_ib = (ts.hour * 60 + ts.minute) - (9 * 60)

        if minutes_since_ib > 0:
            self.expansion_speed = expansion / minutes_since_ib

        if nq_ratio is not None and es_ratio is not None:
            self.relative_expansion = nq_ratio - es_ratio


    def detect_day_type(
        self,
        timestamp,
        daily_atr,
        closes_outside_ib
    ):

        if self.finalized:
            return self.day_type

        ts = datetime.fromisoformat(timestamp)

        session_range = self.session_high - self.session_low

        # 10:00 early evaluation
        if ts.hour == 10 and ts.minute == 0:

            if (
                self.expansion_ratio >= 0.75
                and self.expansion_speed >= 0.7
                and closes_outside_ib >= 1
            ):
                self.day_type = "trend_candidate"

        # 10:30 confirmation
        if ts.hour == 10 and ts.minute == 30:

            if (
                self.expansion_ratio >= 0.75
                and session_range >= 0.5 * daily_atr
                and closes_outside_ib >= 2
            ):
                self.day_type = "trend"
                self.finalized = True

            elif self.expansion_ratio < 0.5 and closes_outside_ib == 1:
                self.day_type = "reversal"
                self.finalized = True

        # 11:30 range confirmation
        if ts.hour == 11 and ts.minute == 30:

            if session_range < 0.4 * daily_atr:
                self.day_type = "range"
                self.finalized = True

        return self.day_type