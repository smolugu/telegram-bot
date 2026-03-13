from datetime import datetime


def get_7h_label(timestamp):

    dt = datetime.fromisoformat(timestamp)
    h = dt.hour

    if 1 <= h < 8:
        return "1AM"

    if 8 <= h < 15:
        return "8AM"

    if 15 <= h < 22:
        return "3PM"

    return None


class SevenHourCandle:

    def __init__(self, label):

        self.label = label
        self.reset()

    def reset(self):

        self.open = None
        self.high = None
        self.low = None
        self.close = None

        self.body = None
        self.upper_wick = None
        self.lower_wick = None

        self.bias = None

        # IB levels (mainly for 8AM block)
        self.ib_high = None
        self.ib_low = None
        self.ib_ce = None


    def update(self, candle):

        o = candle["open"]
        h = candle["high"]
        l = candle["low"]
        c = candle["close"]

        if self.open is None:
            self.open = o
            self.high = h
            self.low = l

        else:
            self.high = max(self.high, h)
            self.low = min(self.low, l)

        self.close = c


    def compute_bias(self):

        if None in (self.open, self.high, self.low, self.close):
            return

        self.body = abs(self.close - self.open)

        self.upper_wick = self.high - max(self.open, self.close)
        self.lower_wick = min(self.open, self.close) - self.low

        if self.body > self.upper_wick and self.body > self.lower_wick:

            if self.close > self.open:
                self.bias = "bullish"
            else:
                self.bias = "bearish"

        else:
            self.bias = "neutral"


class SevenHourBuilder:

    def __init__(self):

        self.candles = {
            "1AM": SevenHourCandle("1AM"),
            "8AM": SevenHourCandle("8AM"),
            "3PM": SevenHourCandle("3PM")
        }

        self.current_label = None


    def update(self, candle):

        label = get_7h_label(candle["timestamp"])

        if label is None:
            return

        # new 7h block starting
        if label != self.current_label:

            if self.current_label is not None:
                self.candles[self.current_label].compute_bias()

            self.candles[label].reset()
            self.current_label = label

        # update active candle
        self.candles[label].update(candle)



def in_wick_window(timestamp, wick_minutes=60):

    dt = datetime.fromisoformat(timestamp)

    centers = [18, 1, 8, 15]

    for center in centers:

        start = center * 60 - wick_minutes
        end = center * 60 + wick_minutes

        minutes_now = dt.hour * 60 + dt.minute

        if start <= minutes_now <= end:
            return True, center

    return False, None