# Three Main Day Types
# 1. Trend Day
#  - IB breaks early
#  - Price stays outside IB
#  - range expands steadily
#  - Favor continuation, avoid reversals

# 2. Reversal Day
#  - London Sweep
#  - Ny reverses direction
#  - Closes inside IB after sweep
#  - Ob forms inside IB

# 3. Range Day
#  - IB not broken
#  - Price oscillates inside range
#  - ATR expansion low
#  - small targets, avoid breakouts

# Inputs needed: IB_high, IB_low, Ny_am bias, daily ATR, current range
from datetime import datetime

# Market Context based on IB, ATR and other IB metrics
class MarketContext:

    def __init__(self, instrument, label = "NY AM"):

        self.instrument = instrument
        self.label = label

        self.reset()
        
    
    def reset(self):
        self.ib_high = None
        self.ib_low = None
        self.ib_range = None
        self.ib_ce = None
        self.ib_ready = False
        self.current_above_ib = 0
        self.current_below_ib = 0
        self.max_above_ib = 0
        self.max_below_ib = 0
        self.ib_containment_count = 0

        self.session_high = None
        self.session_low = None
        self.session_open = None
        self.session_close = None
        self.session_range = None
        self.session_direction = None
        self.directional_move = None
        self.efficiency = None

        self.daily_atr = None
        self.atr_usage = None
        self.overnight_atr_usage = None
        self.atr_context = None
        self.atr_used_above_open = False
        self.atr_used_below_open = False
        self.directional_exhaustion = None
        self.atr_daily_bias = "neutral"
        self.no_bearish_expansion_below_open = False
        self.no_bullish_expansion_above_open = False
        

        

        # compression
        self.compression_flags = {
            "nested_1_in_18": False,
            "engulfing_1_over_18": False,
            "overlap_1_18": False,
            "overlap_8_1": False,
            "nested_8_between_18_1": False,
            "multi_ib_compression": False
            }
        self.compression_range = {"high": None, "low": None}

        # smt
        self.bullish_smt_1d = None
        self.bullish_smt_7h = None
        self.bearish_smt_1d = None
        self.bearish_smt_7h = None
        self.bullish_smt_1h = None
        self.bearish_smt_1h = None  
        self.bullish_smt_30m = None 
        self.bearish_smt_30m = None
        self.bullish_key_level_smt = None
        self.bearish_key_level_smt = None
        
        self.atr_expansion_ratio = None
        self.expansion_origin = None
        self.overnight_expansion = False

        self.day_type = None
        self.day_type_finalized = False
        self.bias = "neutral"
        self.expansion_ratio = 0
        self.expansion_speed = 0
        self.relative_expansion = 0
        self.exhaustion = False

    # Lunch decision engine
    # def is_retracement(self):
    #     return (self.day_type == "trend"
    #             and self.expansion_speed > 0.5
    #             and self.atr_usage < 1.0
    #             and self.acceptance_outside_ib == True)
    
    # def is_reversal(self):
    #     return(
    #         self.art_usage >=0.9 
    #         and self.expansion_speed < 0.5
    #         and self.failed_acceptance == True
    #         and self.liquidity_sweep == True
    #     )

    # def is_lunch_breakout(self):
    #     return (
    #         self.expansion_type == "overnight_dominant"
    #         and self.ib_containment_count >= 5
    #         and self.breakout_from_ib == True
    #         )
    
    # def lunch_decision(self):
    #     if self.is_reversal(self):
    #         return "reversal_trade"
    #     elif self.is_retracement(self):
    #         return "continuation_trade"
    #     elif self.is_lunch_breakout(self):
    #         return "breakout_trade"
    #     else:
    #         return "no_trade"


    def values(self):
        return {
            # "instrument": self.instrument,
            "atr": self.daily_atr,
            # "label": self.label,
            "bias": self.bias,
            "atr_usage": self.atr_usage,
            "day_type": self.day_type,
            # "ib_high": self.ib_high,
            # "ib_low": self.ib_low,
            "current_above_ib": self.current_above_ib,
            "current_below_ib": self.current_below_ib,
            "max_above_ib": self.max_above_ib,
            "max_below_ib": self.max_below_ib,
            "current_day_high": self.session_high,
            "current_day_low": self.session_low,
            "atr_expansion_ratio": self.atr_expansion_ratio,
            "expansion_ratio": self.expansion_ratio,
            "expansion_speed": self.expansion_speed,
            "relative_expansion": self.relative_expansion,
            "session_direction": self.session_direction,
            "session_high": self.session_high,
            "session_low": self.session_low,
            "session_open": self.session_open,
            "session_close": self.session_close,
        }

    def set_ib(self, ib_high, ib_low):

        self.ib_high = ib_high
        self.ib_low = ib_low
        self.ib_range = ib_high - ib_low
        self.ib_ce = (ib_high + ib_low) / 2
        self.ib_ready = True


    def update_compression_info(self, compression_flags, compression_range):
        self.compression_flags = compression_flags
        self.compression_range = compression_range

    def update_session_range(self, high, low, open, close):

        if self.session_open is None:
            self.session_open = open
        self.session_close = close

        if self.session_high is None:
            self.session_high = high
            self.session_low = low
        else:
            self.session_high = max(self.session_high, high)
            self.session_low = min(self.session_low, low)
        self.session_range = self.session_high - self.session_low
        # direction
        self.session_direction = "bullish" if self.session_close > self.session_open else "bearish"
        # print("session high: ", self.session_high)
        # print("sessionlow: ", self.session_low)
        # print("session range: ", self.session_range)
        # print("atrusage: ", self.atr_usage)
        # print("daily atr: ", self.daily_atr)
    
    def set_daily_atr(self, atr):
        self.daily_atr = atr

    def update_atr_usage(self, current_30m_start, close=None):
        """
        Updates:
        - ATR usage
        - overnight exhaustion
        - directional exhaustion
        - efficiency
        - daily bias
        """

        print("session_range: ", self.session_range)
        print("daily_atr: ", self.daily_atr)

        ts = datetime.fromisoformat(current_30m_start)

        # =====================================================
        # BASIC ATR USAGE
        # =====================================================
        
        self.atr_usage = (
            self.session_range / self.daily_atr
            if self.daily_atr
            else 0
        )
        # self.atr_usage = self.session_range / self.daily_atr
        
        # =====================================================
        # OVERNIGHT EXHAUSTION CHECK
        # =====================================================
        if ts.hour == 9 and ts.minute == 30:

            self.overnight_atr_usage = self.atr_usage

            if self.overnight_atr_usage > 0.8:
                self.atr_context = "overnight_exhaustion"
                self.expansion_origin = "overnight"
                self.overnight_expansion = True

        # =====================================================
        # DIRECTIONAL ATR USAGE
        # =====================================================
        self.range_used_above_open = 0
        self.range_used_below_open = 0

        if self.session_open is not None:

            # ---------------------------------------------
            # RANGE USED ABOVE DAILY OPEN
            # ---------------------------------------------
            if self.session_high > self.session_open:
                self.range_used_above_open = (
                    self.session_high - self.session_open
                )

            # ---------------------------------------------
            # RANGE USED BELOW DAILY OPEN
            # ---------------------------------------------
            if self.session_low < self.session_open:
                self.range_used_below_open = (
                    self.session_open - self.session_low
                )

        # Normalize by ATR
        self.atr_used_above_open = (
            self.range_used_above_open / self.daily_atr
            if self.daily_atr
            else 0
        )

        self.atr_used_below_open = (
            self.range_used_below_open / self.daily_atr
            if self.daily_atr
            else 0
        )

        # =====================================================
        # DIRECTIONAL EXHAUSTION
        # =====================================================
        self.directional_exhaustion = None

        # Strong bullish expansion already happened
        if self.atr_used_above_open >= 0.8:
            self.directional_exhaustion = "bullish"

        # Strong bearish expansion already happened
        elif self.atr_used_below_open >= 0.8:
            self.directional_exhaustion = "bearish"

        # =====================================================
        # DAILY BIAS
        # =====================================================
        self.atr_daily_bias = "neutral"

        # Bias based on directional efficiency + location
        if (
            self.atr_used_above_open > self.atr_used_below_open
            and self.atr_used_above_open >= 0.4
        ):
            self.atr_daily_bias = "bullish"

        elif (
            self.atr_used_below_open > self.atr_used_above_open
            and self.atr_used_below_open >= 0.4
        ):
            self.atr_daily_bias = "bearish"

        # =====================================================
        # DIRECTIONAL MOVE / EFFICIENCY
        # =====================================================
        self.directional_move = None
        self.efficiency = None

        if close is not None and self.session_open is not None:

            current_price = close
            net_move = abs(current_price - self.session_open)
            self.directional_move = (
                net_move / self.daily_atr
                if self.daily_atr
                else 0
            )

            # ---------------------------------------------
            # EFFICIENCY
            # > 0.7 = trending
            # 0.4-0.7 = mixed
            # < 0.4 = choppy
            # ---------------------------------------------
            self.efficiency = (
                self.directional_move / self.atr_usage
                if self.atr_usage > 0
                else None
            )

        # =====================================================
        # CONTEXT FLAGS
        # =====================================================

        # Prevent bearish expansion below open
        self.no_bearish_expansion_below_open = False

        if (
            self.directional_exhaustion == "bullish"
            # and close is not None
            # and close < self.session_open
        ):
            self.no_bearish_expansion_below_open = True

        # Prevent bullish expansion above open
        self.no_bullish_expansion_above_open = False

        if (
            self.directional_exhaustion == "bearish"
            # and close is not None
            # and close > self.session_open
        ):
            self.no_bullish_expansion_above_open = True

        # =====================================================
        # DEBUG
        # =====================================================
        # print(
        #     f"""
        #     {self.instrument}

        #     daily_atr: {self.daily_atr}
        #     atr_usage: {self.atr_usage}

        #     session_high: {self.session_high}
        #     session_low: {self.session_low}
        #     session_open: {self.session_open}

        #     atr_used_above_open: {self.atr_used_above_open}
        #     atr_used_below_open: {self.atr_used_below_open}

        #     directional_exhaustion: {self.directional_exhaustion}

        #     atr_daily_bias: {self.atr_daily_bias}

        #     directional_move: {self.directional_move}
        #     efficiency: {self.efficiency}

        #     atr_context: {self.atr_context}

        #     no_bearish_expansion_below_open:
        #         {self.no_bearish_expansion_below_open}

        #     no_bullish_expansion_above_open:
        #         {self.no_bullish_expansion_above_open}
        #     """
        # )
    def get_atr_info(self):
        return {
            "instrument": self.instrument,
            "daily_atr": self.daily_atr,
            "atr_usage": self.atr_usage,
            "session_high": self.session_high,
            "session_low": self.session_low,
            "session_open": self.session_open,
            "session_close": self.session_close,
            "session_range_below": (self.session_open - self.session_low) if self.session_low is not None and self.session_open is not None else None,
            "session_range_above": (self.session_high - self.session_open) if self.session_high is not None and self.session_open is not None else None,
            "atr_used_above_open": self.atr_used_above_open,
            "atr_used_below_open": self.atr_used_below_open,
            "directional_exhaustion": self.directional_exhaustion,
            "atr_daily_bias": self.atr_daily_bias,
            "directional_move": self.directional_move,
            "efficiency": self.efficiency,
            "atr_context": self.atr_context,
            "no_bearish_expansion_below_open": self.no_bearish_expansion_below_open,
            "no_bullish_expansion_above_open": self.no_bullish_expansion_above_open,

        }

    def update_atr_usage_old(self, current_30m_start, close=None):
        print("session_range: ", self.session_range)
        print("dauly_atr: ", self.daily_atr)
        ts = datetime.fromisoformat(current_30m_start)
        if ts.hour == 9 and ts.minute == 30:
            self.overnight_atr_usage = self.session_range / self.daily_atr
            if self.overnight_atr_usage > 0.8:
                self.atr_context = "overnight exhaustion"
                self.expansion_origin = "overnight"
                self.overnight_expansion = True
        self.atr_usage = self.session_range / self.daily_atr
        # efficiency
        # > 0.7 - clean trend, 0.4-0.7 mixed, < 0.4 choppy
        if close is not None and self.session_open is not None:
            current_price = close
            net_move = abs(current_price - self.session_open)
            self.directional_move = abs(net_move) / self.daily_atr
            self.efficiency = (self.directional_move / self.atr_usage if self.atr_usage > 0 else None)

        print(f"{self.instrument} daily atr: ", self.daily_atr, " atr usage: ", self.atr_usage, " sessio high: ", self.session_high, " session low: ", self.session_low, " atr context: ", self.atr_context)

    def update_1h_smt(self, bullish_smt_1h, bearish_smt_1h):
        self.bullish_smt_1h = bullish_smt_1h
        self.bearish_smt_1h = bearish_smt_1h

    def update_1h_smt_status(self, last_closed_nq, last_closed_es):
        if self.bullish_smt_1h is not None:
            if self.bullish_smt_1h["sweeper"] == "nq":
                if last_closed_es["low"] < self.bullish_smt_1h["es_level_price"]:
                    self.bullish_smt_1h = None  # invalidate bullish smt if price has moved against it
            elif self.bullish_smt_1h["sweeper"] == "es":
                if last_closed_nq["low"] < self.bullish_smt_1h["nq_level_price"]:
                    self.bullish_smt_1h = None  # invalidate bullish smt if price has moved against it

        if self.bearish_smt_1h is not None:
            if self.bearish_smt_1h["sweeper"] == "nq":
                if last_closed_es["high"] > self.bearish_smt_1h["es_level_price"]:
                    self.bearish_smt_1h = None  # invalidate bearish smt if price has moved against it
            elif self.bearish_smt_1h["sweeper"] == "es":
                if last_closed_nq["high"] > self.bearish_smt_1h["nq_level_price"]:
                    self.bearish_smt_1h = None  # invalidate bearish smt if price has moved against it
        
    def update_ib_acceptance(self, close):
        if close > self.ib_high:
            self.current_above_ib += 1
            self.current_below_ib = 0
            self.max_above_ib += 1
        elif close < self.ib_low:
            self.current_below_ib += 1
            self.current_above_ib = 0
            self.max_below_ib += 1
        else:
            self.current_above_ib = 0
            self.current_below_ib = 0
            self.ib_containment_count += 1

    def compute_expansion_metrics(
        self,
        timestamp,
        nq_ratio=None,
        es_ratio=None
    ):

        ts = datetime.fromisoformat(timestamp)

        bullish = max(0, self.session_high - self.ib_high)
        bearish = max(0, self.ib_low - self.session_low)

        expansion = max(bullish, bearish)

        if self.ib_range > 0:
            self.expansion_ratio = expansion / self.ib_range

        minutes_since_ib = (ts.hour * 60 + ts.minute) - (9 * 60)

        if minutes_since_ib > 0:
            self.expansion_speed = expansion / minutes_since_ib

        # if nq_ratio is not None and es_ratio is not None:
        #     self.relative_expansion = nq_ratio - es_ratio

    def update_relative_expansion(self, other_expansion_ratio):
        self.relative_expansion = (self.expansion_ratio - other_expansion_ratio)

    
            
    
    def detect_day_type(
        self,
        # last_closed_candle
        timestamp,
        current_timestamp,
        close
        # closes_outside_ib
    ):
        ts = datetime.fromisoformat(current_timestamp)

        session_range = self.session_high - self.session_low
        # print("MC hour: Min - ", ts.hour, ":", ts.minute)

        # PM Trend - late range expansion
        # pre market expansion -> ny am range -> PM expansion
        if ts.minute >= 0 and (ts.hour == 14  or ts.hour == 15):
            # print("MC hour: Min - ", ts.hour, ":", ts.minute)
            # print("ib containment count: ", self.ib_containment_count)
            # print("day_type: ", self.day_type)
            if (
                self.day_type == "range"
                and self.ib_containment_count >= 6
            ):
                if close > self.ib_high:
                    self.day_type = "range_expansion"
                    self.bias = "bullish"
                elif close < self.ib_low:
                    self.day_type = "range_expansion"
                    self.bias = "bearish"

        
        if self.day_type_finalized or self.daily_atr is None:
            return self.day_type
        if self.session_high is None or self.session_low is None:
            return self.day_type
    

        # 10:00 early evaluation
        if ts.hour == 10 and ts.minute == 0:

            if (
                self.expansion_ratio >= 0.75
                and self.expansion_speed >= 0.7
                and (self.current_above_ib >= 1 or self.current_below_ib >=1)
            ):
                self.day_type = "trend_candidate"
                print("updating bias at 10am")
                if self.current_above_ib >= 1:
                    self.bias = "bullish"
                    print("trend_candidate: assigning bullish at 10am")
                elif self.current_below_ib >=1 :
                    self.bias = "bearish"
                    print("trend candidate: assigning bearish at 10am")

        # 10:30 confirmation
        if ts.hour == 10 and ts.minute == 30:
            print("expansion ratio: ", self.expansion_ratio)
            print("expansion speed: ", self.expansion_speed)
            print("atr usage: ", self.atr_usage)
            if (self.expansion_ratio >= 1.2 and self.atr_usage > 0.9 and self.expansion_speed < 0.5):
                self.exhaustion = True
                print("assigning exhaustion at 10:30am")
                print("assigning day type: ", self.day_type)
                print("finalizing day type: ", self.day_type_finalized)
                if self.exhaustion:
                    self.day_type = "reversal"
                    self.day_type_finalized = True
                    #  boost score for exhaustion and reversal by 15 points

            elif (
                0.75 <= self.expansion_ratio <= 1.2
                and session_range >= 0.5 * self.daily_atr
                and (self.max_above_ib >= 2 or self.max_below_ib >= 2)
            ):
                self.day_type = "trend"
                self.day_type_finalized = True
                print("assigning day type to trend at 10:30am")
                print("max_above_ib: ", self.max_above_ib)
                print("max_below_ib: ", self.max_below_ib)
                if self.max_above_ib >= 2:
                    self.bias = "bullish"
                    print("trend: assigning bullish at 10:30am")
                    
                else:
                    self.bias = "bearish"
                    print("trend: assigning bearish at 10:30am")

            elif 0.2 < self.expansion_ratio < 0.5 and (self.max_above_ib == 1 or self.max_below_ib == 1):
                self.day_type = "reversal"
                self.day_type_finalized = True
                print("max_above_ib: ", self.max_above_ib)
                print("max_below_ib: ", self.max_below_ib)
                print("assigning day type to reversal at 10:30am")
                
                if self.max_above_ib == 1:
                    self.bias = "bullish"
                    print("max_above_ib == 1. assigning bullish at 10:30am")
                else:
                    self.bias = "bearish"
                    print("max_above_ib == 1. assigning bearish at 10:30am")

        # 11:30 range confirmation
        if ts.hour == 11 and ts.minute == 30:
            print("session range: ", self.session_range)
            print("daily atr 0.4%: ", 0.4*self.daily_atr)
            print("current_above_ib: ", self.current_above_ib)
            print("current_below_ib: ", self.current_below_ib)
            print("day_type: ", self.day_type)
            print("bias: ", self.bias)

            if session_range < 0.4 * self.daily_atr and (self.current_above_ib == 0 and self.current_below_ib == 0):
                self.day_type = "range"
                print("assigning day type  to range at 11:30am")
                self.day_type_finalized = True
                self.bias = "neutral"
                print("assigning bias to neutral at 11:30am")

        return self.day_type