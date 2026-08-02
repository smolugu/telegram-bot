class IBContinuationCandidate:

    def __init__(self, instrument):
        self.instrument = instrument
        self.reset()

    def reset(self):

        self.ib_high = None
        self.ib_low = None
        self.ib_ce = None
        self.ib_ready = False

        self.bullish_active = False
        self.bearish_active = False

        self.displacement_timestamp = None

        self.retest_confirmed = False
        self.alert_sent = False

    def update(self, values):
        self.ib_low = values["ib_low"]
        self.ib_high = values["ib_high"]
        self.ib_ce = values["ib_ce"]
        self.ib_ready = values["ib_ready"]
