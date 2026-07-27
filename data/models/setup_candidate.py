import uuid

class SetupCandidate:

    def __init__(self, side, instrument):
        self.side = side  # "buy_side" or "sell_side"
        self.instrument = instrument
        self.id =  uuid.uuid4().hex[:8]
        
        self.reset()

    def reset(self):
        # if instrument:
        #     self.instrument = instrument
        self.active = False
        self.id = uuid.uuid4().hex[:8]
        self.sweep_timestamp = None
        self.sweep_candle_extreme = None
        self.sweep_3m_timestamp = None
        self.sweep_and_ob_confirmed = False
        self.sweep_and_ob_ce_confirmed = False
        self.sweep_and_ob_entry = None
        self.sweep_and_ob_ce_entry = None
        self.sweep_and_ob_confirmation_timestamp = None
        self.swept_levels = None
        self.sweep_key_level = False
        self.sweep_level = None
        self.sweep_type = None
        self.caution = False
        self.is_breakout_rejection = False
        self.check_breakout_rejection = False
        self.sweep_candle = None
        self.ib_entry = None
        self.ib_stop_loss = None

        self.smt_confirmed = False
        self.smt_timestamp = None

        self.ob_confirmed = False
        self.final_ob_confirmed = False
        self.ob_data = None
        self.ob_level = None
        self.is_level_rejection = False
        self.rejection_ob_level = None

        self.fvg_confirmed = False
        self.fvg_data = None

        self.confirmation_time = None
        self.alert_sent = False
        self.window_name = None
        self.trade_status = None
        self.insert_trade_data = None
        self.ping_type = None
        self.initial_target = None
        self.initial_target_price = None
        self.final_target = None
        self.final_target_price = None
        

    # --------------------------------------------------

    def set_ib_entry(self, entry, stop_loss):
        self.ib_entry = entry
        self.ib_stop_loss = stop_loss

    # --------------------------------------------------

    def get_sweep_info(self):
        return {
            "sweep_timestamp": self.sweep_timestamp,
            "sweep_candle_extreme": self.sweep_candle_extreme,
            "sweep_3m_timestamp": self.sweep_3m_timestamp,
            "sweep_candle": self.sweep_candle,
            "check_breakout_rejection": self.check_breakout_rejection,
            "is_breakout_rejection": self.is_breakout_rejection,
            "caution": self.caution,
            "sweep_type": self.sweep_type,
            "sweep_level": self.sweep_level,
            "sweep_key_level": self.sweep_key_level,
            "swept_levels": self.swept_levels,
            "sweep_and_ob_confirmation_timestamp": self.sweep_and_ob_confirmation_timestamp,
            "sweep_and_ob_ce_entry": self.sweep_and_ob_ce_entry,
            "sweep_and_ob_entry": self.sweep_and_ob_entry,
            "sweep_and_ob_ce_confirmed": self.sweep_and_ob_ce_confirmed,
            "sweep_and_ob_confirmed": self.sweep_and_ob_confirmed,
        }
    
    def register_sweep(self, sweep_data):
        # timestamp, sweep_candle_extreme, sweep_time, sweep_and_ob_confirmed = False, sweep_and_ob_entry = None, sweep_and_ob_ce_confirmed=False, sweep_and_ob_ce_entry=None, sweep_and_ob_confirmation_timestamp = None, swept_levels = None, instrument = None, sweep_type = None, sweep_candle = None, sweep_level = None, caution=False
        
        self.reset()
        self.active = True
        self.sweep_timestamp = sweep_data["timestamp"]
        self.sweep_candle_extreme = sweep_data["sweep_candle_extreme"]
        self.sweep_3m_timestamp = sweep_data["sweep_time"]
        self.sweep_and_ob_confirmed = sweep_data["sweep_and_ob_confirmed"]
        self.sweep_and_ob_entry = sweep_data["sweep_and_ob_entry"]
        self.sweep_and_ob_ce_confirmed = sweep_data["sweep_and_ob_ce_confirmed"]
        self.sweep_and_ob_ce_entry = sweep_data["sweep_and_ob_ce_entry"]
        self.sweep_and_ob_confirmation_timestamp = sweep_data["sweep_and_ob_confirmation_timestamp"]
        self.confirmation_time = sweep_data["sweep_and_ob_confirmation_timestamp"]
        self.swept_levels = sweep_data["swept_levels"]
        self.sweep_key_level = sweep_data["sweep_key_level"]
        self.sweep_type = sweep_data["sweep_type"]
        self.check_breakout_rejection = sweep_data["sweep_type"] == "breakout"
        self.instrument = sweep_data["instrument"]
        self.sweep_candle = sweep_data["sweep_candle"]
        self.sweep_level = sweep_data["sweep_level"]
        self.caution = sweep_data["caution"]
        self.ob_level = sweep_data["ob_level"]
        self.is_level_rejection = sweep_data["is_level_rejection"]
        self.rejection_ob_level = sweep_data["rejection_ob_level"]

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
        self.confirmation_time = ob_data["confirmation_timestamp"]
        self.ob_level = ob_data["ob_level"] if self.ob_level is None else self.ob_level

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
