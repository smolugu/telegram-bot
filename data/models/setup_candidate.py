class SetupCandidate:

    def __init__(self, side):
        self.side = side  # "buy_side" or "sell_side"

        self.reset()

    def reset(self):
        self.active = False
        
        self.sweep_timestamp = None
        self.sweep_candle_extreme = None
        self.sweep_3m_timestamp = None

        self.smt_confirmed = False
        self.smt_timestamp = None

        self.ob_confirmed = False
        self.ob_data = None

        self.fvg_confirmed = False
        self.fvg_data = None

        self.alert_sent = False

    # --------------------------------------------------

    def register_sweep(self, timestamp, sweep_candle_extreme, sweep_time):
        self.reset()
        self.active = True
        self.sweep_timestamp = timestamp
        self.sweep_candle_extreme = sweep_candle_extreme
        self.sweep_3m_timestamp = sweep_time

    # --------------------------------------------------

    def register_smt(self, timestamp):
        if not self.active:
            return
        self.smt_confirmed = True
        self.smt_timestamp = timestamp

    # --------------------------------------------------

    def register_ob(self, ob_data):
        if not self.active:
            return
        self.ob_confirmed = True
        self.ob_data = ob_data

    # --------------------------------------------------

    def register_fvg(self, fvg_data):
        if not self.active:
            return
        self.fvg_confirmed = True
        self.fvg_data = fvg_data

    # --------------------------------------------------

    def is_ready(self):
        return (
            self.active
            and self.smt_confirmed
            and self.ob_confirmed
            and self.fvg_confirmed
            and not self.alert_sent
        )

    # --------------------------------------------------

    def mark_alert_sent(self):
        self.alert_sent = True

    # --------------------------------------------------

    def invalidate(self):
        self.reset()
