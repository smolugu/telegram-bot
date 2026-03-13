class IBContinuationCandidate:

    def __init__(self, instrument):

        self.instrument = instrument
        self.reset()

    def reset(self):

        self.active = False
        self.direction = None
        self.displacement_timestamp = None
        self.ib_level = None
        self.retest_confirmed = False
        self.alert_sent = False