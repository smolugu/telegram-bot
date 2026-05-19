class NewYorkMarketContext:

    def __init__(self, instrument, ib_18 = {}, ib_1 = {}):
        
        self.instrument = instrument
        self.ib_18 = ib_18
        self.ib_2 = {}
        self.ib_1 = ib_1
        self.ib_10 = {}
        self.ib_8 = {}
        self.directional_mode = None

        # -------- SUMMARY --------
        self.structure_type = None
        self.delivery = None
        self.preferred_sweep = None
        self.quality = None
        self.note = None

        # -------- STRUCTURE --------
        # Ib_relationship: inside_1am, inside_18, engulfing_1am, engulfing_18, sandwich, above_1_18,
        # partial_overlap_bullish, partial_overlap_neutral, below_1_18, partial_overlap_bearish
        self.structure = {
            "position_vs_1": None,
            "position_vs_18_1": None,
            "ib_relationship": None,
            "ib_relationship_1": None,
            "ib_relationship_18_1": None,
            "ib18_above_ib1": False,
            "ib18_below_ib1": False,
            "compression": False,
            "is_strong_compression": False,
            "range_high": None,
            "range_low": None,
            "range_ce": None,
            "rebalance_level": None,
            "ib_direction_8": None,
            "is_ib_strong_body": False,
            "ib_body_range": None,
            "engulfing_deep_retracement": False,
            "is_staircase": False
        }

        # -------- SWEEP --------
        self.sweep = {
            "side": None,
            "time": None,
            "tier": None,
            "is_external": False,
            "count": 0,
            "count_low": 0,
            "count_high": 0,
            "inducement_level_high": None,
            "inducement_level_low": None,
            "is_smt_low": False,
            "sweeper_low": None,
            "is_smt_high": False,
            "sweeper_high": None,
            "is_valid_sweep": False,
        }

        # -------- ACCEPTANCE --------
        self.acceptance = {
            "status": None,
            "held_outside": False
        }

        # -------- PHASE --------
        self.phase = "init"
    
    def sandwich(self, ib_18, ib_1, ib_8):
    # Step 1: ensure one is fully above the other
        ib18_above_ib1 = (
            ib_18["low"] > ib_1["low"] and
            ib_18["high"] > ib_1["high"]
        )

        ib18_below_ib1 = (
            ib_18["low"] < ib_1["low"] and
            ib_18["high"] < ib_1["high"]
        )

        if not (ib18_above_ib1 or ib18_below_ib1):
            return False

        # Step 2: IB_8 inside combined outer range
        lower_bound = min(ib_18["low"], ib_1["low"])
        upper_bound = max(ib_18["high"], ib_1["high"])

        return (
            ib_8["low"] > lower_bound and
            ib_8["high"] < upper_bound
        )

    # =========================================
    # 1. UPDATE 1AM IB STRUCTURE
    # =========================================
    def set_8am_ib(self, seven_hour_builder_candles, ib_18, ib_1):
        seven_hour_candle_8am = seven_hour_builder_candles["8AM"].values()
        self.ib_8["high"] = seven_hour_candle_8am["ib_high"]
        self.ib_8["low"] = seven_hour_candle_8am["ib_low"]
        self.ib_8["ce"] = seven_hour_candle_8am["ib_ce"]
        self.ib_8["open"] = seven_hour_candle_8am["ib_open"]
        self.ib_8["close"] = seven_hour_candle_8am["ib_close"]
        print("setting ib8am: ", self.ib_8)
        self.ib_18 = ib_18
        self.ib_1 = ib_1
        self.update_ib_relationships()
    
    def set_10am_ib(self, last_closed):
        self.ib_10["high"] = last_closed["high"]
        self.ib_10["low"] = last_closed["low"]
        self.ib_10["ce"] = (last_closed["high"] + last_closed["low"]) / 2
        self.ib_10["open"] = last_closed["open"]
        self.ib_10["close"] = last_closed["close"]
        self.ib_10["direction"] = "bullish" if last_closed["open"] < last_closed["close"] else "bearish"
    
    def update_ib_relationships(self):
        print(" updating ib_8 relationships: ", self.instrument)
        ib18_high = self.ib_18["high"]
        ib18_low = self.ib_18["low"]
        ib1_high = self.ib_1["high"]
        ib1_low = self.ib_1["low"]

        ib8_high = self.ib_8["high"]
        ib8_low = self.ib_8["low"]
        ib8_open = self.ib_8["open"]
        ib8_close = self.ib_8["close"]

        body = abs(ib8_close - ib8_open)
        range_ = ib8_high - ib8_low
        is_strong_body = body/range_ > 0.75
        ib_body_range = body/range_
        self.structure["ib_direction_8"] = "bullish" if ib8_open < ib8_close else "bearish"
        self.structure["is_ib_strong_body"] = is_strong_body
        self.structure["ib_body_range"] = ib_body_range
        # also store in ib_8
        self.ib_8["direction"] = "bullish" if ib8_open < ib8_close else "bearish"
        self.ib_8["is_strong_body"] = is_strong_body

        # relative position of IBs
        self.structure["ib18_above_ib1"] = (
            self.ib_18["low"] > self.ib_1["low"] and
            self.ib_18["high"] > self.ib_1["high"]
        )
        print("ib18_above_ib1: ", self.structure["ib18_above_ib1"])
        print("ib18_low, ib1_low: ", self.ib_18["low"], self.ib_1["low"])
        print("ib18_high, ib1_high: ", self.ib_18["high"], self.ib_1["high"])

        self.structure["ib18_below_ib1"] = (
            self.ib_18["low"] < self.ib_1["low"] and
            self.ib_18["high"] < self.ib_1["high"]
        )


        # -----------------------------------
        # 1. INSIDE 1am IB → compression
        # -----------------------------------
        if ib8_high <= ib1_high and ib8_low >= ib1_low:
            print("compression 1am IB inside 8amIB for: ", self.instrument)
            self.structure["ib_relationship"] = "inside_1am"
            self.structure["compression"] = True
            self.structure["is_strong_compression"] = True

            self.structure["range_high"] = ib1_high
            self.structure["range_low"] = ib1_low
            self.structure["range_ce"] = (ib1_high + ib1_low)/2
        # -----------------------------------
        # 1.1 INSIDE 18 IB → compression
        # -----------------------------------
        elif ib8_high <= ib18_high and ib8_low >= ib18_low:
            print("compression inside 18am IB for: ", self.instrument)
            self.structure["ib_relationship"] = "inside_18"
            self.structure["compression"] = True
            self.structure["is_strong_compression"] = True

            self.structure["range_high"] = ib18_high
            self.structure["range_low"] = ib18_low
            self.structure["range_ce"] = (ib18_high + ib18_low)/2
        # -----------------------------------
        # 2. ENGULFING 1am → expansion happened 
        # -----------------------------------
        elif ib8_high > ib1_high and ib8_low < ib1_low:
            print("engilfing 1am IB for: ", self.instrument)
            self.structure["ib_relationship"] = "engulfing_1am"
            self.structure["compression"] = False
            self.structure["range_high"] = ib8_high
            self.structure["range_low"] = ib8_low
            self.structure["range_ce"] = (ib8_high + ib8_low)/2
        # -----------------------------------
        # 2.1 ENGULFING 18 → expansion happened
        # -----------------------------------
        elif ib8_high > ib18_high and ib8_low < ib18_low:
            print("engilfing 18am IB for: ", self.instrument)
            self.structure["ib_relationship"] = "engulfing_18"
            self.structure["compression"] = False
            self.structure["range_high"] = ib8_high
            self.structure["range_low"] = ib8_low
            self.structure["range_ce"] = (ib8_high + ib8_low)/2
        
        elif self.sandwich(self.ib_18, self.ib_1, self.ib_8):
            print("sandwich IB for: ", self.instrument)
            self.structure["ib_relationship"] = "sandwich"
            self.structure["compression"] = True
            self.structure["is_strong_compression"] = True
            self.structure["range_high"] = max(self.ib_18["high"], self.ib_1["high"])
            self.structure["range_low"] = min(self.ib_18["low"], self.ib_1["low"])
            self.structure["range_ce"] =(self.structure["range_high"] + self.structure["range_low"])/2

        # -----------------------------------
        # 3. ABOVE → directional bullish no overlap 
        # -----------------------------------
        elif ib18_high < ib1_low and ib8_low > ib1_high:
            print("ib18_high: ", ib18_high)
            print("ib1_low: ", ib1_low)
            print("ib8_low: ", ib8_low)
            print("ib1_high: ", ib1_high)
            print("self ib18: ", self.ib_18)
            print("seld ib1: ", self.ib_1)
            print("above directional bullish for: ", self.instrument)
            self.structure["ib_relationship"] = "above_1_18"
            self.structure["compression"] = False

            self.structure["range_high"] = ib8_high
            self.structure["range_low"] = ib8_low
            self.structure["range_ce"] = (ib8_high + ib8_low)/2
        # -----------------------------------
        # 3.1 ABOVE → directional bullish with partial overlap
        # -----------------------------------
        # if ib18_high < ib1_low and ib1_low <= ib8_low <= ib1_high:
        # elif ib18_high < ib1_low and ib8_low in (ib1_low, ib1_high):
        # elif ib18_high < ib1_low and ib1_low <= ib8_low <= ib1_high:
        elif (ib18_high < ib1_low or ib1_low <= ib18_high <= ib1_high) and ib1_low <= ib8_low <= ib1_high:
            print("above directional bullish partial overlap for: ", self.instrument)
        
            self.structure["ib_relationship"] = "partial_overlap_bullish"
            # weak compression
            self.structure["compression"] = True
            self.structure["is_strong_compression"] = False if ib18_high < ib1_low else True
            self.structure["is_staircase"] = ib1_low <= ib18_high <= ib1_high
            self.structure["range_high"] = ib8_high
            self.structure["range_low"] = ib1_low
            self.structure["range_ce"] = (ib1_low + ib8_high)/2
            self.structure["rebalance_level"] = (ib8_high + ib18_low)/2
        # elif ib18_low < ib1_low < ib18_high and ib1_low <= ib8_low <= ib1_high:
        #     print("staircase directional bullish partial overlap for: ", self.instrument)
        
        #     self.structure["ib_relationship"] = "staircase_overlap_bullish"
        #     # weak compression
        #     self.structure["compression"] = True
        #     self.structure["is_strong_compression"] = True
        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib18_low
        #     self.structure["range_ce"] = (ib18_low + ib8_high)/2
        #     self.structure["rebalance_level"] = (ib8_high + ib18_low)/2
        # -----------------------------------
        # 3.2 ABOVE → below 18IB with partial overlap - neutral bias
        # -----------------------------------
        # elif ib18_low > ib1_high and ib8_low in (ib18_low, ib18_high):
        elif (ib18_low > ib1_high or ib1_high >= ib18_low >= ib1_low) and ib18_low <= ib8_low <= ib18_high:
            print("partial_overlap_bullish_neutral for: ", self.instrument)
            self.structure["ib_relationship"] = "partial_overlap_bullish_neutral"
            # weak compression
            self.structure["compression"] = True
            self.structure["is_strong_compression"] = False
            self.structure["range_high"] = ib8_high
            self.structure["range_low"] = ib18_low
            self.structure["range_ce"] = (ib8_high + ib18_low) / 2
            self.structure["rebalance_level"] = (ib1_low + ib8_high) / 2

        elif (ib18_low > ib1_high or ib1_high >= ib18_low >= ib1_low) and ib8_low >= ib18_high:
            print("partial_overlap_bullish_neutral_shallow for : ", self.instrument)
            self.structure["ib_relationship"] = "partial_overlap_bullish_neutral_shallow"
            # weak compression
            self.structure["compression"] = False
            self.structure["is_strong_compression"] = False
            self.structure["range_high"] = ib8_high
            self.structure["range_low"] = ib8_low
            self.structure["range_ce"] = (ib8_high + ib8_low) / 2
            self.structure["rebalance_level"] = (ib1_low + ib8_high) / 2

        # -----------------------------------
        # 4. BELOW → directional bearish no overlap
        # -----------------------------------
        elif ib18_low > ib1_high and ib8_high < ib1_low:
            print("below_1_18 for: ", self.instrument)
            self.structure["ib_relationship"] = "below_1_18"
            self.structure["compression"] = False

            self.structure["range_high"] = ib8_high
            self.structure["range_low"] = ib8_low
            self.structure["range_ce"] = (ib8_high + ib8_low) / 2
            self.structure["rebalance_level"] = (ib18_high + ib8_low) / 2

        # -----------------------------------
        # 4.1 BELOW → directional bearish with partial overlap 
        # -----------------------------------
        # elif ib18_low > ib1_high and ib8_high in (ib1_low, ib1_high):
        elif ib18_low > ib1_high and ib1_low <= ib8_high <= ib1_high:
            print("partial_overlap_bearish for: ", self.instrument)
            self.structure["ib_relationship"] = "partial_overlap_bearish"
            # weak compression
            self.structure["compression"] = True
            self.structure["is_strong_compression"] = False
            self.structure["range_high"] = ib1_high
            self.structure["range_low"] = ib8_low
            self.structure["range_ce"] = (ib1_high + ib8_low) / 2
            self.structure["rebalance_level"] = (ib18_high + ib8_low) / 2
        # elif ib1_high >= ib18_low >= ib1_low and ib1_low <= ib8_high <= ib1_high:
        #     print("staircase_overlap_bearish for: ", self.instrument)
        #     self.structure["ib_relationship"] = "staircase_overlap_bearish"
        #     # weak compression
        #     self.structure["compression"] = True
        #     self.structure["is_strong_compression"] = True
        #     self.structure["range_high"] = ib18_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib18_high + ib8_low) / 2
        #     self.structure["rebalance_level"] = (ib18_high + ib8_low) / 2
        # -----------------------------------
        # 4.2 BELOW → above 18Ib with partial overlap - neutral bias
        # -----------------------------------
        # elif ib18_high < ib1_low and ib8_high in (ib18_high, ib18_low):
        elif (ib18_high < ib1_low or ib1_low <= ib18_high <= ib1_high) and ib18_low <= ib8_high <= ib18_high:
            print("partial_overlap_bearish_neutral (compression -> deep rebalance) for: ", self.instrument)
            self.structure["ib_relationship"] = "partial_overlap_bearish_neutral"
            # weak compression
            self.structure["compression"] = True
            self.structure["is_strong_compression"] = False
            self.structure["range_high"] = ib18_high
            self.structure["range_low"] = ib8_low
            self.structure["range_ce"] = (ib18_high + ib8_low) / 2
            self.structure["rebalance_level"] = (ib1_high + ib8_low) / 2
        elif (ib18_high < ib1_low or ib1_low <= ib18_high <= ib1_high) and ib8_high <= ib18_low:
            print("partial_overlap_bearish_neutral (compression -> shallow rebalance) for: ", self.instrument)
            self.structure["ib_relationship"] = "partial_overlap_bearish_neutral_shallow"
            # weak compression
            self.structure["compression"] = False
            self.structure["is_strong_compression"] = False
            self.structure["range_high"] = ib8_high
            self.structure["range_low"] = ib8_low
            self.structure["range_ce"] = (ib8_high + ib8_low) / 2
            self.structure["rebalance_level"] = (ib1_high + ib8_low) / 2
        else:
            print("no relation found")
            self.structure["range_high"] = ib8_high
            self.structure["range_low"] = ib8_low
            self.structure["range_ce"] = (ib8_high + ib8_low) / 2
            

        self.directional_mode = self.structure["ib_relationship"] in ["above_1_18", "below_1_18"]
    
    

    # review function
    def classify_structure(self):

        # -----------------------------------------
        # IB8 inside BOTH IB18 and IB1
        # -----------------------------------------
        if (
            self.ib8_inside_ib18
            and self.ib8_inside_ib1
        ):
            return "sandwich_compression"

        # -----------------------------------------
        # IB1 above IB18 + IB8 inside IB1
        # -----------------------------------------
        if (
            self.ib1_above_ib18
            and self.ib8_inside_ib1
        ):
            return "continuation_recompression_bullish"

        # -----------------------------------------
        # IB1 below IB18 + IB8 inside IB1
        # -----------------------------------------
        if (
            self.ib1_below_ib18
            and self.ib8_inside_ib1
        ):
            return "continuation_recompression_bearish"

        # -----------------------------------------
        # failed expansion bullish
        # -----------------------------------------
        if (
            self.ib1_above_ib18
            and self.ib8_overlap_ib18_low
        ):
            return "failed_bullish_expansion"

        # -----------------------------------------
        # failed expansion bearish
        # -----------------------------------------
        if (
            self.ib1_below_ib18
            and self.ib8_overlap_ib18_high
        ):
            return "failed_bearish_expansion"

        return "mixed_overlap"
    
    # review function
    def determine_expected_delivery(self):

        structure = self.structure_type

        # =================================================
        # CONTINUATION RECOMPRESSION
        # =================================================
        if structure == "continuation_recompression_bullish":

            if self.upside_atr_available:

                return {
                    "delivery": "continuation_expansion",
                    "preferred_sweep": "compression_lows",
                    "quality": "rocket_candidate"
                    if self.smt_aligned
                    else "normal_expansion"
                }

            else:

                return {
                    "delivery": "rebalance_only",
                    "quality": "limited"
                }

        # =================================================
        # SANDWICH COMPRESSION
        # =================================================
        if structure == "sandwich_compression":

            return {
                "delivery": "expansion_to_liquidity",
                "preferred_sweep": "either_side",
                "quality": "normal",
                "note": "expect move completion at first liquidity target"
            }

        # =================================================
        # FAILED EXPANSION
        # =================================================
        if structure == "failed_bullish_expansion":

            return {
                "delivery": "sweep_and_reverse",
                "preferred_sweep": "highs_first",
                "quality": "flush_candidate"
                if self.smt_aligned
                else "normal_expansion"
            }

        return {
            "delivery": "mixed",
            "quality": "low_conviction"
        }
    
    # review function
    def generate_summary(self):

        d = self.expected_delivery

        return f'''
            Structure:
            {self.structure_type}

            Expected Delivery:
            {d["delivery"]}

            Preferred Sweep:
            {d.get("preferred_sweep")}

            Expansion Quality:
            {d.get("quality")}

            Notes:
            {d.get("note", "")}
            '''
    # =========================================
    # 2. POSITION RELATIVE TO IB
    # =========================================
    def update_position(self, candle):
        close = candle["close"]

        if close > self.ib_1["high"]:
            self.structure["position_vs_1"] = "above"
        elif close < self.ib_1["low"]:
            self.structure["position_vs_1"] = "below"
        else:
            self.structure["position_vs_1"] = "inside"
    
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
            self.sweep["time"] = candle["timestamp"]
            if self.sweep['count_low'] == 0:
                self.sweep["count_low"] += 1
                self.sweep["count"] += 1
                self.sweep["inducement_level_low"] = low
                
            elif low < self.sweep["inducement_level_low"]:
                self.sweep["count_low"] += 1
                self.sweep["count"] += 1
                self.sweep["inducement_level_low"] = low

            # Priority check
            if levels.get("pdl") and low < levels["pdl"]["price"]:
                self.sweep["level"] = "pdl"
                self.sweep["tier"] = 1
                self.sweep["is_external"] = True

            elif levels.get("london_low") and low < levels["london_low"]["price"]:
                self.sweep["level"] = "london_low"
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
            if self.sweep['count_high'] == 0:
                self.sweep["count_high"] += 1
                self.sweep["count"] += 1
                self.sweep["inducement_level_high"] = high

            elif high > self.sweep["inducement_level_high"]:
                self.sweep["count_high"] += 1
                self.sweep["count"] += 1
                self.sweep["inducement_level_high"] = high

            if levels.get("pdh") and high > levels["pdh"]["price"]:
                self.sweep["level"] = "pdh"
                self.sweep["tier"] = 1
                self.sweep["is_external"] = True

            elif levels.get("london_high") and high > levels["london_high"]["price"]:
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
        low = candle["low"]
        high = candle["high"]
        open = candle["open"]

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
        if self.structure["ib_relationship"] == "engulfing" and self.structure["ib_direction_8"] == "bullish":
            self.structure["engulfing_deep_retracement"] = close < self.ib_8["ce"]
            self.phase = "recompression"
        elif self.structure["ib_relationship"] == "engulfing" and self.structure["ib_direction_8"] == "bearish":
            self.structure["engulfing_deep_retracement"] = close > self.ib_8["ce"]
            self.phase = "recompression"
        
        # update if candle reaches rebalance level
        if self.structure["ib_relationship"] == "partial_overlap_bullish_neutral":
            if self.ib_18["low"] > low >= self.structure["rebalance_level"]:
                self.sweep["is_valid_sweep"] = True
            elif low < self.structure["rebalance_level"] and close > self.structure["rebalance_level"]:
                self.sweep["is_valid_sweep"] = True
            else:
                self.sweep["is_valid_sweep"] = False

        elif self.structure["ib_relationship"] == "partial_overlap_bearish_neutral":
            if self.ib_18["high"] < high <= self.structure["rebalance_level"]:
                self.sweep["is_valid_sweep"] = True
            elif high > self.structure["rebalance_level"] and close < self.structure["rebalance_level"]:
                self.sweep["is_valid_sweep"] = True
            else:
                self.sweep["is_valid_sweep"] = False


    
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
        # self.update_position(candle)
        self.detect_sweep(candle, levels)
        self.update_acceptance(candle)
        self.update_phase()
    
    # =========================================
    # 7. Compression Summary
    # =========================================
    def get_compression_data(self):
        is_compression = False
        compression_range = {"high": None, "low": None}
        is_compression = self.structure["compression"] or self.phase == "recompression"
        compression_range["high"] = self.structure["range_high"]
        compression_range["low"] = self.structure["range_low"]
        return is_compression, compression_range, self.sweep
