class SetupCandidate:

    def __init__(self, side, instrument):
        self.side = side  # "buy_side" or "sell_side"
        self.instrument = instrument
        self.reset()

    def reset(self):
        # if instrument:
        #     self.instrument = instrument
        self.active = False
        self.sweep_timestamp = None
        self.sweep_candle_extreme = None
        self.sweep_3m_timestamp = None
        self.sweep_and_ob_confirmed = False
        self.sweep_and_ob_ce_confirmed = False
        self.sweep_and_ob_entry = None
        self.sweep_and_ob_ce_entry = None
        self.sweep_and_ob_confirmation_timestamp = None

        self.smt_confirmed = False
        self.smt_timestamp = None

        self.ob_confirmed = False
        self.final_ob_confirmed = False
        self.ob_data = None

        self.fvg_confirmed = False
        self.fvg_data = None

        self.alert_sent = False
        self.insert_trade_data = None

    # --------------------------------------------------

    def register_sweep(self, timestamp, sweep_candle_extreme, sweep_time, sweep_and_ob_confirmed=False, sweep_and_ob_entry=None, sweep_and_ob_ce_confirmed=False, sweep_and_ob_ce_entry=None, sweep_and_ob_confirmation_timestamp=None, instrument=None):
        self.reset()
        self.active = True
        self.sweep_timestamp = timestamp
        self.sweep_candle_extreme = sweep_candle_extreme
        self.sweep_3m_timestamp = sweep_time
        self.sweep_and_ob_confirmed = sweep_and_ob_confirmed
        self.sweep_and_ob_entry = sweep_and_ob_entry
        self.sweep_and_ob_ce_confirmed = sweep_and_ob_ce_confirmed
        self.sweep_and_ob_ce_entry = sweep_and_ob_ce_entry
        self.sweep_and_ob_confirmation_timestamp = sweep_and_ob_confirmation_timestamp
        self.instrument = instrument

        

    # --------------------------------------------------

    def register_smt(self, timestamp):
        if not self.active:
            return
        self.smt_confirmed = True
        self.smt_timestamp = timestamp

    # --------------------------------------------------

    def register_ob(self, ob_data):
        # if not self.active:
        #     return
        self.ob_confirmed = True
        self.ob_data = ob_data

    # --------------------------------------------------

    def register_fvg(self, fvg_data):
        # if not self.active:
        #     return
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

    def insert_trade(self, insert_trade_data):
        self.insert_trade_data = insert_trade_data

    def invalidate(self):
        self.reset()
