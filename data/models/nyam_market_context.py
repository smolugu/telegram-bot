from data.models.ib_classification import classify_ib_structure


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
        self.execution_state = {
            "rocket_triggered": False,
            "rocket_completed": False,
            "flush_triggered": False,
            "flush_completed": False,
            "auction_direction": None,     # bullish | bearish
            "auction_locked": False,
            "delivery_complete": False,
        }
        self.auction_phase = None

        # -------- STRUCTURE --------
        # Ib_relationship: inside_1am, inside_18, engulfing_1am, engulfing_18, sandwich, above_1_18,
        # partial_overlap_bullish, partial_overlap_neutral, below_1_18, partial_overlap_bearish
        self.structure = {
            "name": None,
            "group": None,
            "structure_phase": None,
            "auction_phase": None,
            "is_neutral_direction_structure": False,
            "category": None,
            "direction": None,
            "is_staircase": False,
            "migration_strength": None,
            "is_compression": False,
            "is_compression_resolution": False,
            "is_strong_compression": False,
            "range_high_swept": False,
            "range_low_swept": False,
            "compression_strength": None,
            "is_acceptance": False,
            "is_decompression": False,
            "is_reintegration": False,
            "is_rebalance": False,
            "is_value_flip": False,
            "note_internal": None,
            "note": None,
            "context_summary": None,
            "compression_state": {
                "first_sweep": None,      # "high" | "low"
                "second_sweep": None,     # "high" | "low"
                "compression_resolved": False,
                "is_fresh_compression_resolution": False,
                "compression_partially_resolved": False,
            },
            "compression_high": None,
            "compression_low": None,
            "compressison_ce": None,
            "range_high": None,
            "range_low": None,
            "range_ce": None,
            "equilibrium_high": None,
            "equilibrium_low": None,
            "equilibrium_ce": None,   
            "mitigation_level": None,
            "ib_direction_8": None,
            "is_ib_strong_body": False,
            "ib_body_range": None,
            # "bearish_ob_level": None,
            # "bullish_ob_level": None,

            "position_vs_1": None,
            "position_vs_18_1": None,
            "ib_relationship": None,
            "ib_relationship_1": None,
            "ib_relationship_18_1": None,
            "ib18_above_ib1": False,
            "ib18_below_ib1": False,
            "engulfing_deep_retracement": False,
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
    # 1. UPDATE 8AM IB STRUCTURE AND RELATIONSHIPS
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
        upper_wick = ib8_high - max(ib8_open, ib8_close)
        lower_wick = min(ib8_open, ib8_close) - ib8_low
        wick_ratio = min(upper_wick, lower_wick) / max(upper_wick, lower_wick)
        print("body rangexx: ", body/range_)
        is_strong_body = body/range_ > 0.75
        ib_body_range = body/range_
        body_pct = body / range_
        upper_pct = upper_wick / range_
        lower_pct = lower_wick / range_
        self.structure["ib_direction_8"] = "bullish" if ib8_open < ib8_close else "bearish"
        self.structure["is_ib_strong_body"] = is_strong_body
        self.structure["ib_body_range"] = ib_body_range
        # also store in ib_8
        self.ib_8["direction"] = "bullish" if ib8_open < ib8_close else "bearish"
        self.ib_8["is_strong_body"] = is_strong_body
        if body_pct >= 0.75:
            self.ib_8["acceptance"] = "very strong"
        elif body_pct >= 0.5:
            self.ib_8["acceptance"] = "strong"

        elif body_pct <= 0.2:

            if wick_ratio >= 0.5:
                self.ib_8["acceptance"] = "neutral"

            elif upper_wick > lower_wick:
                self.ib_8["acceptance"] = "bearish_rejection"

            else:
                self.ib_8["acceptance"] = "bullish_rejection"

        else:
            self.ib_8["acceptance"] = "moderate"

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
        ib_classification_data = classify_ib_structure(self.ib_18, self.ib_1, self.ib_8)
        print("ib_dataXX: ", ib_classification_data)
        
        self.structure["execution_edge"] = ib_classification_data["execution_edge"]
        self.structure["direction_score"] = ib_classification_data["direction_score"]
        self.structure["migration_score"] = ib_classification_data["migration_score"]
        self.structure["pqs"] = ib_classification_data["pqs"]
        self.structure["reaction_levels"] = ib_classification_data["reaction_levels"]
        self.structure["name"] = ib_classification_data["structure_name"]
        self.structure["structure_phase"] = ib_classification_data["structure_phase"]
        self.structure["auction_phase"] = ib_classification_data["auction_phase"]
        self.structure["group"] = ib_classification_data["structure_group"]
        self.structure["is_neutral_direction_structure"] = ib_classification_data["is_neutral_direction_structure"]
        
        self.structure["category"] = ib_classification_data["category"]
        self.structure["direction"] = ib_classification_data["direction"]
        self.structure["is_compression"] = ib_classification_data["is_compression"]
        self.structure["is_compression_resolution"] = ib_classification_data["is_compression_resolution"]
        self.structure["is_strong_compression"] = ib_classification_data["is_strong_compression"]
        self.structure["compression_strength"] = ib_classification_data["compression_strength"]
        self.structure["is_acceptance"] = ib_classification_data["is_acceptance"]
        self.structure["is_decompression"] = ib_classification_data["is_decompression"]
        self.structure["is_reintegration"] = ib_classification_data["is_reintegration"]
        self.structure["is_rebalance"] = ib_classification_data["is_rebalance"]
        self.structure["is_value_flip"] = ib_classification_data["is_value_flip"]
        self.structure["note"] = ib_classification_data["note"]
        self.structure["note_internal"] = ib_classification_data["note_internal"]
        self.structure["context_summary"] = ib_classification_data["context_summary"]
        self.structure["compression_high"] = ib_classification_data["compression_range"]["high"]
        self.structure["compression_low"] = ib_classification_data["compression_range"]["low"]
        self.structure["compression_ce"] = ib_classification_data["compression_range"]["ce"]
        self.structure["range_high"] = ib_classification_data["range"]["high"]
        self.structure["range_low"] = ib_classification_data["range"]["low"]
        self.structure["range_ce"] = ib_classification_data["range"]["ce"]
        self.structure["equilibrium_high"] = ib_classification_data["equilibrium_range"]["high"]
        self.structure["equilibrium_low"] = ib_classification_data["equilibrium_range"]["low"]
        self.structure["equilibrium_ce"] = ib_classification_data["equilibrium_range"]["ce"]
        self.structure["mitigation_level"] = ib_classification_data["mitigation_level"]
        self.structure["migration_strength"] = ib_classification_data["migration_strength"]
        self.structure["is_staircase"] = ib_classification_data["is_staircase"]

        # # -----------------------------------
        # # 1. INSIDE 1am IB → compression
        # # -----------------------------------
        # if ib8_high <= ib1_high and ib8_low >= ib1_low:
        #     print("compression 1am IB inside 8amIB for: ", self.instrument)
        #     self.structure["ib_relationship"] = "inside_1am"
        #     self.structure["compression"] = True
        #     self.structure["is_strong_compression"] = True

        #     self.structure["range_high"] = ib1_high
        #     self.structure["range_low"] = ib1_low
        #     self.structure["range_ce"] = (ib1_high + ib1_low)/2
        # # -----------------------------------
        # # 1.1 INSIDE 18 IB → compression
        # # -----------------------------------
        # elif ib8_high <= ib18_high and ib8_low >= ib18_low:
        #     print("compression inside 18am IB for: ", self.instrument)
        #     self.structure["ib_relationship"] = "inside_18"
        #     self.structure["compression"] = True
        #     self.structure["is_strong_compression"] = True

        #     self.structure["range_high"] = ib18_high
        #     self.structure["range_low"] = ib18_low
        #     self.structure["range_ce"] = (ib18_high + ib18_low)/2
        # # -----------------------------------
        # # 2. ENGULFING 1am → expansion happened 
        # # -----------------------------------
        # elif ib8_high > ib1_high and ib8_low < ib1_low:
        #     print("engilfing 1am IB for: ", self.instrument)
        #     self.structure["ib_relationship"] = "engulfing_1am"
        #     self.structure["compression"] = False
        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib8_high + ib8_low)/2
        # # -----------------------------------
        # # 2.1 ENGULFING 18 → expansion happened
        # # -----------------------------------
        # elif ib8_high > ib18_high and ib8_low < ib18_low:
        #     print("engilfing 18am IB for: ", self.instrument)
        #     self.structure["ib_relationship"] = "engulfing_18"
        #     self.structure["compression"] = False
        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib8_high + ib8_low)/2
        
        # elif self.sandwich(self.ib_18, self.ib_1, self.ib_8):
        #     print("sandwich IB for: ", self.instrument)
        #     self.structure["ib_relationship"] = "sandwich"
        #     self.structure["compression"] = True
        #     self.structure["is_strong_compression"] = True
        #     self.structure["range_high"] = max(self.ib_18["high"], self.ib_1["high"])
        #     self.structure["range_low"] = min(self.ib_18["low"], self.ib_1["low"])
        #     self.structure["range_ce"] =(self.structure["range_high"] + self.structure["range_low"])/2

        # # -----------------------------------
        # # 3. ABOVE → directional bullish no overlap 
        # # -----------------------------------
        # elif ib18_high < ib1_low and ib8_low > ib1_high:
        #     print("ib18_high: ", ib18_high)
        #     print("ib1_low: ", ib1_low)
        #     print("ib8_low: ", ib8_low)
        #     print("ib1_high: ", ib1_high)
        #     print("self ib18: ", self.ib_18)
        #     print("seld ib1: ", self.ib_1)
        #     print("above directional bullish for: ", self.instrument)
        #     self.structure["ib_relationship"] = "above_1_18"
        #     self.structure["compression"] = False

        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib8_high + ib8_low)/2
        # # -----------------------------------
        # # 3.1 ABOVE → directional bullish with partial overlap
        # # -----------------------------------
        # # if ib18_high < ib1_low and ib1_low <= ib8_low <= ib1_high:
        # # elif ib18_high < ib1_low and ib8_low in (ib1_low, ib1_high):
        # # elif ib18_high < ib1_low and ib1_low <= ib8_low <= ib1_high:
        # elif (ib18_high < ib1_low or ib1_low <= ib18_high <= ib1_high) and ib1_low <= ib8_low <= ib1_high:
        #     print("above directional bullish partial overlap for: ", self.instrument)
        
        #     self.structure["ib_relationship"] = "partial_overlap_bullish"
        #     # weak compression
        #     self.structure["compression"] = True
        #     self.structure["is_strong_compression"] = False if ib18_high < ib1_low else True
        #     self.structure["is_staircase"] = ib1_low <= ib18_high <= ib1_high
        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib1_low
        #     self.structure["range_ce"] = (ib1_low + ib8_high)/2
        #     self.structure["rebalance_level"] = (ib8_high + ib18_low)/2
        # # elif ib18_low < ib1_low < ib18_high and ib1_low <= ib8_low <= ib1_high:
        # #     print("staircase directional bullish partial overlap for: ", self.instrument)
        
        # #     self.structure["ib_relationship"] = "staircase_overlap_bullish"
        # #     # weak compression
        # #     self.structure["compression"] = True
        # #     self.structure["is_strong_compression"] = True
        # #     self.structure["range_high"] = ib8_high
        # #     self.structure["range_low"] = ib18_low
        # #     self.structure["range_ce"] = (ib18_low + ib8_high)/2
        # #     self.structure["rebalance_level"] = (ib8_high + ib18_low)/2
        # # -----------------------------------
        # # 3.2 ABOVE → below 18IB with partial overlap - neutral bias
        # # -----------------------------------
        # # elif ib18_low > ib1_high and ib8_low in (ib18_low, ib18_high):
        # elif (ib18_low > ib1_high or ib1_high >= ib18_low >= ib1_low) and ib18_low <= ib8_low <= ib18_high:
        #     print("partial_overlap_bullish_neutral for: ", self.instrument)
        #     self.structure["ib_relationship"] = "partial_overlap_bullish_neutral"
        #     # weak compression
        #     self.structure["compression"] = True
        #     self.structure["is_strong_compression"] = False
        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib18_low
        #     self.structure["range_ce"] = (ib8_high + ib18_low) / 2
        #     self.structure["rebalance_level"] = (ib1_low + ib8_high) / 2

        # elif (ib18_low > ib1_high or ib1_high >= ib18_low >= ib1_low) and ib8_low >= ib18_high:
        #     print("partial_overlap_bullish_neutral_shallow for : ", self.instrument)
        #     self.structure["ib_relationship"] = "partial_overlap_bullish_neutral_shallow"
        #     # weak compression
        #     self.structure["compression"] = False
        #     self.structure["is_strong_compression"] = False
        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib8_high + ib8_low) / 2
        #     self.structure["rebalance_level"] = (ib1_low + ib8_high) / 2

        # # -----------------------------------
        # # 4. BELOW → directional bearish no overlap
        # # -----------------------------------
        # elif ib18_low > ib1_high and ib8_high < ib1_low:
        #     print("below_1_18 for: ", self.instrument)
        #     self.structure["ib_relationship"] = "below_1_18"
        #     self.structure["compression"] = False

        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib8_high + ib8_low) / 2
        #     self.structure["rebalance_level"] = (ib18_high + ib8_low) / 2

        # # -----------------------------------
        # # 4.1 BELOW → directional bearish with partial overlap 
        # # -----------------------------------
        # # elif ib18_low > ib1_high and ib8_high in (ib1_low, ib1_high):
        # elif ib18_low > ib1_high and ib1_low <= ib8_high <= ib1_high:
        #     print("partial_overlap_bearish for: ", self.instrument)
        #     self.structure["ib_relationship"] = "partial_overlap_bearish"
        #     # weak compression
        #     self.structure["compression"] = True
        #     self.structure["is_strong_compression"] = False
        #     self.structure["range_high"] = ib1_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib1_high + ib8_low) / 2
        #     self.structure["rebalance_level"] = (ib18_high + ib8_low) / 2
        # # elif ib1_high >= ib18_low >= ib1_low and ib1_low <= ib8_high <= ib1_high:
        # #     print("staircase_overlap_bearish for: ", self.instrument)
        # #     self.structure["ib_relationship"] = "staircase_overlap_bearish"
        # #     # weak compression
        # #     self.structure["compression"] = True
        # #     self.structure["is_strong_compression"] = True
        # #     self.structure["range_high"] = ib18_high
        # #     self.structure["range_low"] = ib8_low
        # #     self.structure["range_ce"] = (ib18_high + ib8_low) / 2
        # #     self.structure["rebalance_level"] = (ib18_high + ib8_low) / 2
        # # -----------------------------------
        # # 4.2 BELOW → above 18Ib with partial overlap - neutral bias
        # # -----------------------------------
        # # elif ib18_high < ib1_low and ib8_high in (ib18_high, ib18_low):
        # elif (ib18_high < ib1_low or ib1_low <= ib18_high <= ib1_high) and ib18_low <= ib8_high <= ib18_high:
        #     print("partial_overlap_bearish_neutral (compression -> deep rebalance) for: ", self.instrument)
        #     self.structure["ib_relationship"] = "partial_overlap_bearish_neutral"
        #     # weak compression
        #     self.structure["compression"] = True
        #     self.structure["is_strong_compression"] = False
        #     self.structure["range_high"] = ib18_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib18_high + ib8_low) / 2
        #     self.structure["rebalance_level"] = (ib1_high + ib8_low) / 2
        # elif (ib18_high < ib1_low or ib1_low <= ib18_high <= ib1_high) and ib8_high <= ib18_low:
        #     print("partial_overlap_bearish_neutral (compression -> shallow rebalance) for: ", self.instrument)
        #     self.structure["ib_relationship"] = "partial_overlap_bearish_neutral_shallow"
        #     # weak compression
        #     self.structure["compression"] = False
        #     self.structure["is_strong_compression"] = False
        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib8_high + ib8_low) / 2
        #     self.structure["rebalance_level"] = (ib1_high + ib8_low) / 2
        # else:
        #     print("no relation found")
        #     self.structure["range_high"] = ib8_high
        #     self.structure["range_low"] = ib8_low
        #     self.structure["range_ce"] = (ib8_high + ib8_low) / 2
            

        self.directional_mode = self.structure["ib_relationship"] in ["above_1_18", "below_1_18"]
    
    
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
            self.range_low_swept = True
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
            self.range_high_swept = True
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
        if (self.structure["ib_relationship"] == "engulfing" or self.structure["category"] == "decompression") and self.structure["ib_direction_8"] == "bullish":
            self.structure["engulfing_deep_retracement"] = close < self.ib_8["ce"]
            self.phase = "recompression"
        elif (self.structure["ib_relationship"] == "engulfing" or self.structure["category"] == "decompression") and self.structure["ib_direction_8"] == "bearish":
            self.structure["engulfing_deep_retracement"] = close > self.ib_8["ce"]
            self.phase = "recompression"
        
        # update if candle reaches rebalance (mitigation or equilibrium) level
        if self.structure["name"] == "bearish_reintegration" or self.structure["ib_relationship"] == "partial_overlap_bullish_neutral": 
            if self.ib_18["low"] > low >= self.structure["mitigation_level"]:
                self.sweep["is_valid_sweep"] = True
            elif low < self.structure["mitigation_level"] and close > self.structure["mitigation_level"]:
                self.sweep["is_valid_sweep"] = True
            else:
                self.sweep["is_valid_sweep"] = False

        elif self.structure["name"] == "bullish_reintegration" or self.structure["ib_relationship"] == "partial_overlap_bearish_neutral":
            if self.ib_18["high"] < high <= self.structure["mitigation_level"]:
                self.sweep["is_valid_sweep"] = True
            elif high > self.structure["mitigation_level"] and close < self.structure["mitigation_level"]:
                self.sweep["is_valid_sweep"] = True
            else:
                self.sweep["is_valid_sweep"] = False


    
    # =========================================
    # 5. DETERMINE MARKET PHASE
    # =========================================
    def update_phase(self):
        if self.structure["is_compression"] and self.sweep["count"] == 0:
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
    # 7. Compression state
    # =========================================
    def update_compression_state(self, liquidity_level):
        if liquidity_level["cr8am_high"]["swept"] and not liquidity_level["cr8am_low"]["swept"]:
            self.structure["compression_state"]["first_sweep"] = "high"
            self.structure["compression_state"]["compression_partially_resolved"] = True
        elif not liquidity_level["cr8am_high"]["swept"] and liquidity_level["cr8am_low"]["swept"]:
            self.structure["compression_state"]["first_sweep"] = "low"
            self.structure["compression_state"]["compression_partially_resolved"] = True
        elif liquidity_level["cr8am_high"]["swept"] and liquidity_level["cr8am_low"]["swept"]:
            if self.structure["compression_state"]["first_sweep"] == "high":
                self.structure["compression_state"]["second_sweep"] = "low"
            else:
                self.structure["compression_state"]["second_sweep"] = "high"
            if not self.structure["compression_state"]["compression_resolved"]:
                self.structure["compression_state"]["compression_resolved"] = True
                self.structure["compression_state"]["is_fresh_compression_resolution"] = True
            else:
                self.structure["compression_state"]["is_fresh_compression_resolution"] = False

        
    # =========================================
    # 8. Compression Summary
    # =========================================
    def get_compression_data(self):
        is_compression = False
        compression_range = {"high": None, "low": None}
        is_compression = self.structure["is_compression"] or self.phase == "recompression"
        compression_range["high"] = self.structure["compression_high"]
        compression_range["low"] = self.structure["compression_low"]
        return is_compression, compression_range, self.sweep, self.structure["compression_state"]
