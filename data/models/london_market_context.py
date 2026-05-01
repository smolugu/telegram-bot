class LondonMarketContext:

    def __init__(self, instrument, ib_18=None):
        
        self.instrument = instrument
        self.ib_18 = ib_18
        self.ib_2 = None
        self.ib_1 = None
        # self.ib_2 = None
        self.directional_mode = None


        # -------- STRUCTURE --------
        self.structure = {
            "position_vs_18": None,
            "ib_relationship": None,
            "compression": False,
            "is_strong_compression": False,
            "range_high": None,
            "range_low": None,
            "ib_direction_1": None,
            "is_strong_body": False,
            "ib_body_range": None,
            "engulfing_deep_retracement": False
        }

        # -------- SWEEP --------
        self.sweep = {
            "side": None,
            "time": None,
            "is_external": False,
            "count": 0
        }

        # -------- ACCEPTANCE --------
        self.acceptance = {
            "status": None,
            "held_outside": False
        }

        # -------- PHASE --------
        self.phase = "init"

    # =========================================
    # 1. UPDATE 1AM IB STRUCTURE
    # =========================================
    def set_18_1am_ibs(self, seven_hour_builder_candles):
        seven_hour_candle_6pm = seven_hour_builder_candles["6PM"].values()
        seven_hour_candle_1am = seven_hour_builder_candles["1AM"].values()
        self.ib_18["high"] = seven_hour_candle_6pm["ib_high"]
        self.ib_18["low"] = seven_hour_candle_6pm["ib_low"]
        self.ib_18["ce"] = seven_hour_candle_6pm["ib_ce"]
        self.ib_1["high"] = seven_hour_candle_1am["ib_high"]
        self.ib_1["low"] = seven_hour_candle_1am["ib_low"]
        self.ib_1["ce"] = seven_hour_candle_1am["ib_ce"]
        self.ib_1["open"] = seven_hour_candle_1am["ib_open"]
        self.ib_1["close"] = seven_hour_candle_1am["ib_close"]
        self.update_ib_relationships()
    
    def set_2am_ib(self, last_closed):
        self.ib_2["high"] = last_closed["high"]
        self.ib_2["low"] = last_closed["low"]
        self.ib_2["ce"] = (last_closed["high"] + last_closed["low"]) / 2
        self.ib_2["open"] = last_closed["open"]
        self.ib_2["close"] = last_closed["close"]
        self.ib_2["direction"] = "bullish" if last_closed["open"] < last_closed["close"] else "bearish"

    def update_ib_relationships(self):
        ib18_high = self.ib_18["high"]
        ib18_low = self.ib_18["low"]

        ib1_high = self.ib_1["high"]
        ib1_low = self.ib_1["low"]
        ib1_open = self.ib_1["open"]
        ib1_close = self.ib_1["close"]
        body = abs(ib1_close - ib1_open)
        range_ = ib1_high - ib1_low
        is_strong_body = body/range_ > 0.75
        ib_body_range = body/range_

        # -----------------------------------
        # 1. INSIDE → compression
        # -----------------------------------
        if ib1_high <= ib18_high and ib1_low >= ib18_low:
            self.structure["ib_relationship"] = "inside"
            self.structure["compression"] = True
            self.structure["is_strong_compression"] = True

            self.structure["range_high"] = ib18_high
            self.structure["range_low"] = ib18_low

        # -----------------------------------
        # 2. ENGULFING → expansion happened
        # -----------------------------------
        elif ib1_high > ib18_high and ib1_low < ib18_low:
            self.structure["ib_relationship"] = "engulfing"
            self.structure["compression"] = False

            self.structure["range_high"] = ib1_high
            self.structure["range_low"] = ib1_low
            self.structure["ib_direction_1"] = "bullish" if ib1_open < ib1_close else "bearish"
            self.structure["is_strong_body"] = is_strong_body
            self.structure["ib_body_range"] = ib_body_range

        # -----------------------------------
        # 3. ABOVE → directional bullish
        # -----------------------------------
        elif ib1_low > ib18_high:
            self.structure["ib_relationship"] = "above_18"
            self.structure["compression"] = False

            self.structure["range_high"] = ib1_high
            self.structure["range_low"] = ib1_low

        # -----------------------------------
        # 4. BELOW → directional bearish
        # -----------------------------------
        elif ib1_high < ib18_low:
            self.structure["ib_relationship"] = "below_18"
            self.structure["compression"] = False
            

            self.structure["range_high"] = ib1_high
            self.structure["range_low"] = ib1_low

        # -----------------------------------
        # 5. PARTIAL OVERLAP (true overlap)
        # -----------------------------------
        else:
            self.structure["ib_relationship"] = "partial_overlap"

            # treat as weak compression
            self.structure["compression"] = True
            self.structure["is_strong_compression"] = False

            self.structure["range_high"] = max(ib18_high, ib1_high)
            self.structure["range_low"] = min(ib18_low, ib1_low)
        self.directional_mode = self.structure["ib_relationship"] in ["above_18", "below_18"]

    # =========================================
    # 2. POSITION RELATIVE TO IB
    # =========================================
    def update_position(self, candle):
        close = candle["close"]

        if close > self.ib_18["high"]:
            self.structure["position_vs_18"] = "above"
        elif close < self.ib_18["low"]:
            self.structure["position_vs_18"] = "below"
        else:
            self.structure["position_vs_18"] = "inside"

    # =========================================
    # 3. DETECT SWEEP
    # =========================================
    def detect_sweep(self, candle, levels):
        """
        levels = {
            "pdh": value, "pdl": value,
            "asia_high": value, "asia_low": value }
        """

        high = candle["high"]
        low = candle["low"]

        # -------------------------
        # SELL-SIDE SWEEP
        # -------------------------
        if low < self.structure["range_low"]:
            self.sweep["side"] = "sell_side"
            # TODO: fix key candle "time"
            self.sweep["time"] = candle["timestamp"]
            self.sweep["count"] += 1

            # Priority check
            if levels.get("pdl") and low < levels["pdl"]["price"]:
                self.sweep["level"] = "pdl"
                self.sweep["tier"] = 1
                self.sweep["is_external"] = True

            elif levels.get("asia_low") and low < levels["asia_low"]["price"]:
                self.sweep["level"] = "asia_low"
                self.sweep["tier"] = 2
                self.sweep["is_external"] = True

            else:
                self.sweep["level"] = "internal"
                self.sweep["tier"] = 3
                self.sweep["is_external"] = False

        # -------------------------
        # BUY-SIDE SWEEP
        # -------------------------
        elif high > self.structure["range_high"]:
            self.sweep["side"] = "buy_side"
            self.sweep["time"] = candle["timestamp"]
            self.sweep["count"] += 1

            if levels.get("pdh") and high > levels["pdh"]["price"]:
                self.sweep["level"] = "pdh"
                self.sweep["tier"] = 1
                self.sweep["is_external"] = True

            elif levels.get("asia_high") and high > levels["asia_high"]["price"]:
                self.sweep["level"] = "asia_high"
                self.sweep["tier"] = 2
                self.sweep["is_external"] = True

            else:
                self.sweep["level"] = "internal"
                self.sweep["tier"] = 3
                self.sweep["is_external"] = False

    # =========================================
    # 4. ACCEPTANCE LOGIC
    # =========================================
    def update_acceptance(self, candle):
        close = candle["close"]

        if self.sweep["side"] == "sell_side":
            if close < self.structure["range_low"]:
                self.acceptance["status"] = "accepted"
                self.acceptance["held_outside"] = True
            else:
                self.acceptance["status"] = "rejected"

        
        elif self.sweep["side"] == "buy_side":
            if close > self.structure["range_high"]:
                self.acceptance["status"] = "accepted"
                self.acceptance["held_outside"] = True
            else:
                self.acceptance["status"] = "rejected"
        
        # update deep retracement flag for engulfing Ib
        if self.structure["ib_relationship"] == "engulfing" and self.structure["ib_direction_1"] == "bullish":
            self.structure["engulfing_deep_retracement"] = close < self.ib_1["ce"]
        elif self.structure["ib_relationship"] == "engulfing" and self.structure["ib_direction_1"] == "bearish":
            self.structure["engulfing_deep_retracement"] = close > self.ib_1["ce"]


    # =========================================
    # 5. DETERMINE MARKET PHASE
    # =========================================
    def update_phase(self):
        if self.structure["compression"] and self.sweep["count"] == 0:
            self.phase = "compression"

        elif self.sweep["count"] == 1 and self.acceptance["status"] == "rejected":
            self.phase = "inducement"

        elif self.acceptance["status"] == "accepted":
            if self.sweep["count"] == 1:
                self.phase = "expansion"
            else:
                self.phase = "trend"

        elif self.sweep["count"] >= 2 and self.acceptance["status"] == "rejected":
            self.phase = "recompression"
        
    
        if self.sweep["tier"] == 1 and self.acceptance["status"] == "rejected":
            self.phase = "high_confidence_reversal"

    # =========================================
    # 6. MAIN UPDATE PER 30M CANDLE
    # =========================================
    def update(self, candle, levels):
        self.update_position(candle)
        self.detect_sweep(candle, levels)
        self.update_acceptance(candle)
        self.update_phase()

    
    # =========================================
    # 7. ON-DEMAND IB REACTION CHECK (BULLISH)
    # =========================================
    
    def check_bullish_ib_reaction(self, candle):
        return {
            "ib_18": self._bullish_rejection(candle, self.ib_18),
            "ib_1": self._bullish_rejection(candle, self.ib_1) if self.ib_1 else None
        }

    # -----------------------------------------
    # bullish rejection logic:
    # -----------------------------------------
    def _bullish_rejection(self, candle, ib):
        """
        Detect bullish rejection at IB levels using:
        LOW interaction + CLOSE confirmation
        """

        low = candle["low"]
        close = candle["close"]

        ib_high = ib["high"]
        ib_low = ib["low"]
        ib_ce = (ib_high + ib_low) / 2

        result = {
            "reject_low": False,
            "reject_ce": False,
            "reject_high": False,
            "strongest": None,
            "position": None
        }

        # -------------------------
        # POSITION
        # -------------------------
        if close > ib_high:
            result["position"] = "above"
        elif close < ib_low:
            result["position"] = "below"
        else:
            result["position"] = "inside"

        # -------------------------
        # BULLISH REJECTION LOGIC
        # -------------------------

        # Reject LOW
        if low <= ib_low and close > ib_low:
            result["reject_low"] = True

        # Reject CE
        if low <= ib_ce and close > ib_ce:
            result["reject_ce"] = True

        # Reject HIGH (reclaim)
        if low <= ib_high and close > ib_high:
            result["reject_high"] = True

        # -------------------------
        # STRONGEST SIGNAL PRIORITY
        # -------------------------
        if result["reject_low"]:
            result["strongest"] = "low"
        elif result["reject_ce"]:
            result["strongest"] = "ce"
        elif result["reject_high"]:
            result["strongest"] = "high"

        return result
    
    # -----------------------------------------
    # bearish rejection logic:
    # -----------------------------------------
    def _bearish_rejection(self, candle, ib):
        """
        Detect bearish rejection at IB levels using:
        LOW interaction + CLOSE confirmation
        """

        high = candle["high"]
        close = candle["close"]

        ib_high = ib["high"]
        ib_low = ib["low"]
        ib_ce = (ib_high + ib_low) / 2

        result = {
            "reject_low": False,
            "reject_ce": False,
            "reject_high": False,
            "strongest": None,
            "position": None
        }

        # -------------------------
        # POSITION
        # -------------------------
        if close > ib_high:
            result["position"] = "above"
        elif close < ib_low:
            result["position"] = "below"
        else:
            result["position"] = "inside"

        # -------------------------
        # BEARISH REJECTION LOGIC
        # -------------------------

        # Reject LOW
        if high >= ib_low and close < ib_low:
            result["reject_low"] = True

        # Reject CE
        if high >= ib_ce and close < ib_ce:
            result["reject_ce"] = True

        # Reject HIGH (reclaim)
        if high >= ib_high and close < ib_high:
            result["reject_high"] = True

        # -------------------------
        # STRONGEST SIGNAL PRIORITY
        # -------------------------
        if result["reject_low"]:
            result["strongest"] = "low"
        elif result["reject_ce"]:
            result["strongest"] = "ce"
        elif result["reject_high"]:
            result["strongest"] = "high"

        return result
    

    # =========================================
    # Compression Data
    # =========================================
    def get_compression_data(self):
        is_compression = False
        compression_range = None
        is_compression = self.structure["compression"]
        compression_range["high"] = self.structure["range_high"]
        compression_range["low"] = self.structure["range_low"]

        return is_compression, compression_range
    # =========================================
    # DEBUG / OUTPUT
    # =========================================
    def summary(self):
        return {
            "phase": self.phase,
            "structure": self.structure,
            "sweep": self.sweep,
            "acceptance": self.acceptance
        }