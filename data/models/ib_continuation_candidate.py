class IBContinuationCandidate:

    def __init__(self, instrument):
        self.instrument = instrument
        self.reset()

    def reset(self):

        self.ib_high = None
        self.ib_low = None
        self.ib_ce = None

        self.bullish_active = False
        self.bearish_active = False

        self.displacement_timestamp = None

        self.retest_confirmed = False
        self.alert_sent = False