 
def determine_asset_sweep_model(structure):

    structure_name = structure["name"]

    #
    # Compression
    #

    if structure_name in {
        "sandwich_bullish",
        "sandwich_bearish",

        "sandwich_overlap_bullish",
        "sandwich_overlap_bearish",

        "sandwich_partial_overlap_bullish",
        "sandwich_partial_overlap_bearish",

        "bullish_rebalance_compression",
        "bearish_rebalance_compression",

        "sandwich_neutral",

        # weak compression
        "staircase_late_overlap_bullish",
        "staircase_late_overlap_bearish",
    }:
        return "compression"

    #
    # Migration
    #

    if structure_name in {
        "staircase_bullish",
        "staircase_bearish",

        "staircase_gap_bullish",
        "staircase_gap_bearish",

        "staircase_early_overlap_bullish",
        "staircase_early_overlap_bearish",
    }:
        return "migration"

    #
    # Acceptance Decompression
    #

    if structure_name in {
        "bullish_decompression",
        "bearish_decompression",

        "bullish_early_decompression",
        "bearish_early_decompression",
    }:
        return "acceptance_decompression"

    #
    # Rebalance Decompression
    #

    if structure_name in {
        "bullish_macro_decompression",
        "bearish_macro_decompression",
    }:
        return "rebalance_decompression"

    #
    # Mixed Decompression
    #

    if structure_name in {
        "bullish_mixed_decompression",
        "bearish_mixed_decompression",
    }:
        return "mixed_decompression"

    #
    # Reintegration
    #

    if structure_name in {
        "bullish_reintegration",
        "bearish_reintegration",
    }:
        return "reintegration"

    #
    # Value Flip
    #

    if structure_name in {
        "bullish_value_flip",
        "bearish_value_flip",
    }:
        return "value_flip"

    #
    # Fallback
    #

    print(
        f"Unknown structure for sweep model: {structure_name}"
    )

    return "compression"


def validate_sweeps(
        sweep_nq_highs = None,
        sweep_nq_highs_key_level = None,
        sweep_es_highs = None,
        sweep_es_highs_key_level = None,
        sweep_nq_lows = None,
        sweep_nq_lows_key_level = None,
        sweep_es_lows = None,
        sweep_es_lows_key_level = None,
        last_closed_nq = None,
        last_closed_es = None,
        prev_last_closed_nq = None,
        prev_last_closed_es = None,
        nq_ny_market_context = None,
        es_ny_market_context = None,
):
    nq_validation = {
        "highs": {
            "is_valid": False,
            "caution": False,
        },
        "lows" : {
            "is_valid": False,
            "caution": False,
        }
    }
    es_validation = {
        "highs": {
            "is_valid": False,
            "caution": False,
        },
        "lows" : {
            "is_valid": False,
            "caution": False,
        }
    }
    result = {

        "is_valid": False,
        "resolution_type": None,
        "strong_ob_required": False,
        "caution": False,
        "invalid_reason": None,
        "update_or_invlaidate_sweeps": False
    }
    nq_sweep_model = None
    es_sweep_model = None
    nq_validation = None
    es_validation = None
    def _validate_compression_sweeps(instrument, ny_market_context, last_closed, prev_last_closed, sweep_highs, sweep_highs_key_level, sweep_lows, sweep_lows_key_level):
        sweep_rejected_highs = True
        caution_highs = False
        sweep_rejected_lows = True
        caution_lows = False
        is_compression, compression_range, compression_sweep_data = ny_market_context.get_compression_data()
        
        # =================
        # sweep highs block
        # =================
        if (sweep_highs or sweep_highs_key_level) and last_closed["open"] > compression_range["low"] and last_closed["open"] < compression_range["high"]:
            # also captures staircase_overlap_bearish and staircase_overlap_bullish when candle is inside compression zones
            # below we have a separate block for sweep outside compression range and candle outside compression range
            # nq_swept_level = max(sweep_nq_highs["sweep_level"], sweep_nq_highs_key_level["sweep_level"]) if sweep_nq_highs and sweep_nq_highs_key_level else (sweep_nq_highs["sweep_level"] if sweep_nq_highs else sweep_nq_highs_key_level["sweep_level"])
            print("101:")
            swept_level = (
                max(sweep_highs["sweep_level"], sweep_highs_key_level["sweep_level"]) if sweep_highs is not None and sweep_highs_key_level is not None
                else sweep_highs["sweep_level"] if sweep_highs is not None
                else sweep_highs_key_level["sweep_level"] if sweep_highs_key_level is not None
                else None
            )
            if swept_level < compression_range["high"] and last_closed["high"] < compression_range["high"]:
                print("asset Sweep at highs rejected due to compression. invalidating sweep inside compression range")
                print("1011:")
                # sweep_nq_highs = None
                # sweep_nq_highs_key_level = None
                # here rejected highs implies price is still inside compression range
                sweep_rejected_highs = True
            elif compression_sweep_data["count_high"] == 1 and ny_market_context.structure["range_low_swept"]:
                print("1012-1:")
                # price already swept compression low and is out of inducement phase, 
                # so expect sharp rejection because of liquidity
                sweep_rejected_highs = False

            elif compression_sweep_data["count_high"] >= 2:
                print("1012:")
                # here count_high == 1 => inducecment level
                # count_high >=2 => sweep of inducement level => actual move
                sweep_rejected_highs = False
            else:
                print("1013:")
                # here nq swept keylevel and compression high, inducement is not confirmed
                # disallow sweep if the breakout is less than 10 points on nq and less than 
                # 3 points on ES
                sweep_rejected_highs = False
                tol_points = 10 if instrument == "NQ" else 3
                if abs(last_closed["high"] - compression_range["high"]) < tol_points:
                    print("1014:")
                    print("Asset sweep at highs accepted but price near compression range. exercise caution")
                    # add caution flag to sweep as the sweep is not deep and could be inducement
                    # dont invalidate the sweep but use extra confirmation at final trade filter
                    sweep_rejected_highs = False
                    caution_highs = True
                    if sweep_highs is not None:
                        sweep_highs["caution"] = True
                    if sweep_highs_key_level is not None:
                        sweep_highs_key_level["caution"] = True
            if instrument == "NQ":
                nq_validation["highs"]["is_valid"] = not sweep_rejected_highs
                nq_validation["highs"]["caution"] = caution_highs
            else:
                es_validation["highs"]["is_valid"] = not sweep_rejected_highs
                es_validation["highs"]["caution"] = caution_highs
        # =================
        # sweep lows block
        # =================
        if (sweep_lows or sweep_lows_key_level) and last_closed["open"] > compression_range["low"] and last_closed["open"] < compression_range["high"]:
            print("sweep_lows: ", sweep_lows)
            print("104:")
            if sweep_lows is not None:
                print("sweep_lows: ", sweep_lows["sweep_level"])
            print("sweep_lows_key_level: ", sweep_lows_key_level)
            print("last_closed: ", last_closed)
            print("compression_range: ", compression_range)
            # nq_swept_level = min(sweep_lows["sweep_level"], sweep_lows_key_level["sweep_level"]) if sweep_lows and sweep_lows_key_level else (sweep_lows["sweep_level"] if sweep_lows else sweep_lows_key_level["sweep_level"])
            invalidate_sweeps_lows = True
            swept_level = (
                min(sweep_lows["sweep_level"], sweep_lows_key_level["sweep_level"])
                if sweep_lows is not None and sweep_lows_key_level is not None
                else sweep_lows["sweep_level"] if sweep_lows is not None
                else sweep_lows_key_level["sweep_level"] if sweep_lows_key_level is not None
                else None
            )
            print("swept level 1: ", swept_level)
            print("com r low 2: ", compression_range["low"])
            print("last closed low 3: ", last_closed["low"])
            
            if swept_level > compression_range["low"] and last_closed["low"] > compression_range["low"]:
                print("Asset Sweep at lows rejected due to compression. invalidating sweep inside compression range")
                print("section 4")
                # sweep_lows = None
                # sweep_lows_key_level = None
                sweep_rejected_lows = True
            elif compression_sweep_data["count_low"] == 1 and ny_market_context.structure["range_high_swept"]:
                print("1012-1:")
                # price already swept compression low and is out of inducement phase, 
                # so expect sharp rejection because of liquidity
                sweep_rejected_lows = False
            elif compression_sweep_data["count_low"] >= 2:
                print("section 5")
                # if sweep is previous candle low then be cautious, wait for displacement or one more sweep
                # caution if sweep is previus candle lows
                
                # print("prev_to_last_closed: ", prev_last_closed["low"])
                # if swept_level == prev_last_closed["low"]:
                #     print("section 5.1")
                #     sweep_rejected_lows = True
                # else:
                #     sweep_rejected_lows = False
                sweep_rejected_lows = False
            else:
                print("section 6")
                sweep_rejected_lows = False
                print("compression_range: ", compression_range)
                print("last_closed: ", last_closed["low"])
                tol_points = 10 if instrument == "NQ" else 3
                if abs(last_closed["low"] - compression_range["low"]) < tol_points:
                    print("section 7")
                    print("Asset sweep at lows accepted but price near compression range. exercise caution: ", abs(last_closed["low"] - compression_range["low"]))
                    # add caution flag to sweep as the sweep is not deep and could be inducement
                    # dont invalidate the sweep but use extra confirmation at final trade filter
                    sweep_rejected_lows = False
                    caution_lows = True
                    if sweep_lows is not None:
                        sweep_highs["caution"] = True
                    if sweep_highs_key_level is not None:
                        sweep_highs_key_level["caution"] = True
            if instrument == "NQ":
                nq_validation["lows"]["is_valid"] = not sweep_rejected_lows
                nq_validation["lows"]["caution"] = caution_lows
            else:
                es_validation["lows"]["is_valid"] = not sweep_rejected_lows
                es_validation["lows"]["caution"] = caution_lows
        
    def _validate_reintegration_sweeps(instrument, ny_market_context, last_closed, prev_last_closed, sweep_highs, sweep_highs_key_level, sweep_lows, sweep_lows_key_level):
        print("reintegration sweep validation")
        caution_highs = False
        caution_lows = False
        if ny_market_context.structure["name"] == "bearish_reintegration":
            print("sweep validation of bearish reintegration")
            is_valid_sweep_low = False
            is_valid_sweep_high  = False
            # bearish reintegration
            # sweep lows block - compression low, compression low - mitigaltion level zone, mitigation level
            
            if (sweep_lows or sweep_lows_key_level):
                if ny_market_context.structure["compression_low"] > last_closed["low"] > ny_market_context.structure["mitigation_level"]:
                    print("sweep at lows accepted as valid reintegration sweep")
                    is_valid_sweep_low = True
                elif last_closed["low"] < ny_market_context.structure["mitigation_level"] and last_closed["close"] > ny_market_context.structure["mitigation_level"]:
                    print("sweep at lows accepted as valid reintegration sweep")
                    is_valid_sweep_low = True
                else:
                    print("sweep at lows rejected")
                    is_valid_sweep_low = False
                if instrument == "NQ":
                    nq_validation["lows"]["is_valid"] = is_valid_sweep_low
                    nq_validation["lows"]["caution"] = caution_lows
                else:
                    es_validation["lows"]["is_valid"] = is_valid_sweep_low
                    es_validation["lows"]["caution"] = caution_lows
            # sweep highs block
            if (sweep_highs or sweep_highs_key_level):
            
                if last_closed["high"] > ny_market_context.structure["compression_high"]:
                    # is valid sweep with additional confirmations
                    is_valid_sweep_high = True
                    if instrument == "NQ":
                        nq_validation["highs"]["is_valid"] = is_valid_sweep_high
                        nq_validation["highs"]["caution"] = caution_highs
                    else:
                        es_validation["highs"]["is_valid"] = is_valid_sweep_high
                        es_validation["highs"]["caution"] = caution_highs
            
        elif ny_market_context.structure["name"] == "bullish_reintegration":
            print("sweep validation of bullish reintegration")
            is_valid_sweep_low = False
            is_valid_sweep_high = False        
            # bullish reintegration
            # sweep highs block - compression high, compression high - mitigaltion level zone, mitigation level
            if (sweep_highs or sweep_highs_key_level):
                if ny_market_context.structure["compression_high"] < last_closed["high"] < ny_market_context.structure["mitigation_level"]:
                    print("sweep at compression highs accepted as valid reintegration sweep")
                    is_valid_sweep_high = True
                elif last_closed["high"] > ny_market_context.structure["mitigation_level"] and last_closed["close"] < ny_market_context.structure["mitigation_level"]:
                    print("sweep at highs, mitigation level accepted as valid reintegration sweep")
                    is_valid_sweep_high = True
                else:
                    print("sweep at highs is not ready")
                    is_valid_sweep_high = False
                if instrument == "NQ":
                    nq_validation["highs"]["is_valid"] = is_valid_sweep_high
                    nq_validation["highs"]["caution"] = caution_highs
                else:
                    es_validation["highs"]["is_valid"] = is_valid_sweep_high
                    es_validation["highs"]["caution"] = caution_highs
            # sweep lows block
            if (sweep_lows or sweep_lows_key_level):            
                if last_closed["low"] < ny_market_context.structure["compression_low"]:
                    # is valid sweep with additional confirmations
                    is_valid_sweep_low = True
                    if instrument == "NQ":
                        nq_validation["lows"]["is_valid"] = is_valid_sweep_low
                        nq_validation["lows"]["caution"] = caution_lows
                    else:
                        es_validation["lows"]["is_valid"] = is_valid_sweep_low
                        es_validation["lows"]["caution"] = caution_lows

    def _validate_migration_sweeps(instrument, ny_market_context, last_closed, prev_last_closed, sweep_highs, sweep_highs_key_level, sweep_lows, sweep_lows_key_level):
        print("migration sweep validation")
    def _validate_acceptance_decompression_sweeps(instrument, ny_market_context, last_closed, prev_last_closed, sweep_highs, sweep_highs_key_level, sweep_lows, sweep_lows_key_level):
        print("acceptance decompression sweep validation")
        if ny_market_context.structure["name"] == "bullish_decompression":
            print("sweep validation of bullish decompression")
            is_valid_sweep_low = False
            is_valid_sweep_high = False
            # longs
            # 
            if (sweep_lows or sweep_lows_key_level):
                print("")

            # shorts


    def _validate_rebalance_decompression_sweeps(instrument, ny_market_context, last_closed, prev_last_closed, sweep_highs, sweep_highs_key_level, sweep_lows, sweep_lows_key_level):
        print("rebalance decompression sweep validation")
    def _validate_mixed_decompression_sweeps(instrument, ny_market_context, last_closed, prev_last_closed, sweep_highs, sweep_highs_key_level, sweep_lows, sweep_lows_key_level):
        print("mixed decompression sweep validation")
    def _validate_value_flip_sweeps(instrument, ny_market_context, last_closed, prev_last_closed, sweep_highs, sweep_highs_key_level, sweep_lows, sweep_lows_key_level):
        print("value flip sweep validation")
        # bearish value flip
        caution_highs = False
        caution_lows = False
        if ny_market_context.structure["name"] == "bearish_value_flip":
            print("sweep validation of bearish value flip")
            is_valid_sweep_low = False
            is_valid_sweep_high = False        
            # longs
            # sweep lows block - ib8 low, ib8 low - mitigaltion level zone, mitigation level
            if (sweep_lows or sweep_lows_key_level):
                if last_closed["low"] < ny_market_context.ib_8["low"] and last_closed["close"] > ny_market_context.ib_8["low"]:
                    print("sweep at lows, ib8 low accepted as valid value flip sweep")
                    is_valid_sweep_low = True
                elif last_closed["low"] < ny_market_context.structure["mitigation_level"] and last_closed["close"] > ny_market_context.structure["mitigation_level"]:
                    print("sweep at lows, mitigation level accepted as valid value flip sweep")
                    is_valid_sweep_low = True
                else:
                    print("sweep at lows, no valid value flip sweep found")
                if instrument == "NQ":
                    nq_validation["lows"]["is_valid"] = is_valid_sweep_low
                    nq_validation["lows"]["caution"] = caution_lows
                else:
                    es_validation["lows"]["is_valid"] = is_valid_sweep_low
                    es_validation["lows"]["caution"] = caution_lows
            # shorts
            # sweep highs block - above ib8 high, PDH and at atr exhaustion (atr exhaustion at final check)
            if (sweep_highs or sweep_highs_key_level):
                if last_closed["high"] > ny_market_context.ib_8["high"]:
                    print("sweep at highs, ib8 high accepted as valid value flip sweep")
                    is_valid_sweep_high = True
                else:
                    print("sweep at highs, no valid value flip sweep found")
                    is_valid_sweep_high = False

                if instrument == "NQ":
                    nq_validation["highs"]["is_valid"] = is_valid_sweep_high
                    nq_validation["highs"]["caution"] = caution_highs
                else:
                    es_validation["highs"]["is_valid"] = is_valid_sweep_high
                    es_validation["highs"]["caution"] = caution_highs

        # bearish value flip
        elif ny_market_context.structure["name"] == "bullish_value_flip":
            print("sweep validation of bullish value flip")
            is_valid_sweep_low = False
            is_valid_sweep_high = False        
            # shorts
            # sweep highs block - ib8 high, ib8 high - mitigaltion level zone, mitigation level
            if (sweep_highs or sweep_highs_key_level):
                if last_closed["high"] > ny_market_context.ib_8["high"] and last_closed["close"] < ny_market_context.ib_8["high"]:
                    print("sweep at highs, ib8 high accepted as valid value flip sweep")
                    is_valid_sweep_high = True
                elif last_closed["high"] > ny_market_context.structure["mitigation_level"] and last_closed["close"] < ny_market_context.structure["mitigation_level"]:
                    print("sweep at highs, mitigation level accepted as valid value flip sweep")
                    is_valid_sweep_high = True
                else:
                    print("sweep at highs, no valid value flip sweep found")
                if instrument == "NQ":
                    nq_validation["highs"]["is_valid"] = is_valid_sweep_high
                    nq_validation["highs"]["caution"] = caution_highs
                else:
                    es_validation["highs"]["is_valid"] = is_valid_sweep_high
                    es_validation["highs"]["caution"] = caution_highs
            # longs
            # sweep lows block - above ib8 low, PDL and at atr exhaustion (atr exhaustion at final check)
            if (sweep_lows or sweep_lows_key_level):
                if last_closed["low"] < ny_market_context.ib_8["low"]:
                    print("sweep at lows, ib8 low accepted as valid value flip sweep")
                    is_valid_sweep_low = True
                else:
                    print("sweep at lows, no valid value flip sweep found")
                    is_valid_sweep_low = False

                if instrument == "NQ":
                    nq_validation["lows"]["is_valid"] = is_valid_sweep_low
                    nq_validation["lows"]["caution"] = caution_lows
                else:
                    es_validation["lows"]["is_valid"] = is_valid_sweep_low
                    es_validation["lows"]["caution"] = caution_lows

    def validate_asset_sweeps(instrument, sweep_model):
        if sweep_model == "compression":
            # based on instrument, send values
            if instrument == "NQ":
                _validate_compression_sweeps(
                    instrument= instrument, ny_market_context=nq_ny_market_context, last_closed=last_closed_nq, prev_last_closed=prev_last_closed_nq , sweep_highs=sweep_nq_highs, sweep_highs_key_level=sweep_nq_highs_key_level, sweep_lows=sweep_nq_lows, sweep_lows_key_level=sweep_nq_lows_key_level
                )
            elif instrument == "ES":
                _validate_compression_sweeps(
                    instrument= instrument, ny_market_context=es_ny_market_context, last_closed=last_closed_es, prev_last_closed=prev_last_closed_es , sweep_highs=sweep_es_highs, sweep_highs_key_level=sweep_es_highs_key_level, sweep_lows=sweep_es_lows, sweep_lows_key_level=sweep_es_lows_key_level
                )

        elif sweep_model == "migration":
            if instrument == "NQ":
                _validate_migration_sweeps(
                    instrument=instrument, ny_market_context=nq_ny_market_context, last_closed=last_closed_nq, prev_last_closed=prev_last_closed_nq , sweep_highs=sweep_nq_highs, sweep_highs_key_level=sweep_nq_highs_key_level, sweep_lows=sweep_nq_lows, sweep_lows_key_level=sweep_nq_lows_key_level
                )
            elif instrument == "ES":
                _validate_migration_sweeps(
                    instrument=instrument, ny_market_context=es_ny_market_context, last_closed=last_closed_es, prev_last_closed=prev_last_closed_es , sweep_highs=sweep_es_highs, sweep_highs_key_level=sweep_es_highs_key_level, sweep_lows=sweep_es_lows, sweep_lows_key_level=sweep_es_lows_key_level
                )

        elif sweep_model == "acceptance_decompression":
            if instrument == "NQ":
                _validate_acceptance_decompression_sweeps(
                    instrument=instrument, ny_market_context=nq_ny_market_context, last_closed=last_closed_nq, prev_last_closed=prev_last_closed_nq , sweep_highs=sweep_nq_highs, sweep_highs_key_level=sweep_nq_highs_key_level, sweep_lows=sweep_nq_lows, sweep_lows_key_level=sweep_nq_lows_key_level
                )
            elif instrument == "ES":
                _validate_acceptance_decompression_sweeps(
                    instrument=instrument, ny_market_context=es_ny_market_context, last_closed=last_closed_es, prev_last_closed=prev_last_closed_es , sweep_highs=sweep_es_highs, sweep_highs_key_level=sweep_es_highs_key_level, sweep_lows=sweep_es_lows, sweep_lows_key_level=sweep_es_lows_key_level
                )
        
        elif sweep_model == "rebalance_decompression":
            if instrument == "NQ":
                _validate_rebalance_decompression_sweeps(
                    instrument=instrument, ny_market_context=nq_ny_market_context, last_closed=last_closed_nq, prev_last_closed=prev_last_closed_nq , sweep_highs=sweep_nq_highs, sweep_highs_key_level=sweep_nq_highs_key_level, sweep_lows=sweep_nq_lows, sweep_lows_key_level=sweep_nq_lows_key_level
                )
            elif instrument == "ES":
                _validate_rebalance_decompression_sweeps(
                    instrument=instrument, ny_market_context=es_ny_market_context, last_closed=last_closed_es, prev_last_closed=prev_last_closed_es , sweep_highs=sweep_es_highs, sweep_highs_key_level=sweep_es_highs_key_level, sweep_lows=sweep_es_lows, sweep_lows_key_level=sweep_es_lows_key_level
                )

        elif sweep_model == "mixed_decompression":
            if instrument == "NQ":
                _validate_mixed_decompression_sweeps(
                    instrument=instrument, ny_market_context=nq_ny_market_context, last_closed=last_closed_nq, prev_last_closed=prev_last_closed_nq , sweep_highs=sweep_nq_highs, sweep_highs_key_level=sweep_nq_highs_key_level, sweep_lows=sweep_nq_lows, sweep_lows_key_level=sweep_nq_lows_key_level
                )
            elif instrument == "ES":
                _validate_mixed_decompression_sweeps(
                    instrument=instrument, ny_market_context=es_ny_market_context, last_closed=last_closed_es, prev_last_closed=prev_last_closed_es , sweep_highs=sweep_es_highs, sweep_highs_key_level=sweep_es_highs_key_level, sweep_lows=sweep_es_lows, sweep_lows_key_level=sweep_es_lows_key_level
                )

        elif sweep_model == "reintegration":
            if instrument == "NQ":
                _validate_reintegration_sweeps(
                    instrument=instrument, ny_market_context=nq_ny_market_context, last_closed=last_closed_nq, prev_last_closed=prev_last_closed_nq , sweep_highs=sweep_nq_highs, sweep_highs_key_level=sweep_nq_highs_key_level, sweep_lows=sweep_nq_lows, sweep_lows_key_level=sweep_nq_lows_key_level
                )
            elif instrument == "ES":
                _validate_reintegration_sweeps(
                    instrument=instrument, ny_market_context=es_ny_market_context, last_closed=last_closed_es, prev_last_closed=prev_last_closed_es , sweep_highs=sweep_es_highs, sweep_highs_key_level=sweep_es_highs_key_level, sweep_lows=sweep_es_lows, sweep_lows_key_level=sweep_es_lows_key_level
                )

        elif sweep_model == "value_flip":
            if instrument == "NQ":
                _validate_value_flip_sweeps(
                    instrument=instrument, ny_market_context=nq_ny_market_context, last_closed=last_closed_nq, prev_last_closed=prev_last_closed_nq , sweep_highs=sweep_nq_highs, sweep_highs_key_level=sweep_nq_highs_key_level, sweep_lows=sweep_nq_lows, sweep_lows_key_level=sweep_nq_lows_key_level
                )
            elif instrument == "ES":
                _validate_value_flip_sweeps(
                    instrument=instrument, ny_market_context=es_ny_market_context, last_closed=last_closed_es, prev_last_closed=prev_last_closed_es , sweep_highs=sweep_es_highs, sweep_highs_key_level=sweep_es_highs_key_level, sweep_lows=sweep_es_lows, sweep_lows_key_level=sweep_es_lows_key_level
                )

    # step 1: determine sweep model for each asset

    nq_sweep_model = determine_asset_sweep_model(nq_ny_market_context.structure)
    es_sweep_model = determine_asset_sweep_model(es_ny_market_context.structure)

    # step 2: validate sweeps based on sweep model
    nq_validation = validate_asset_sweeps(
        asset_name="NQ",
        sweep_model=nq_sweep_model,
    )

    es_validation = validate_asset_sweeps(
        asset_name="ES",
        sweep_model=es_sweep_model,
    )

    
    return {
        "NQ": {
            "sweep_model": nq_sweep_model,
            "validation": nq_validation,
        },
        "ES": {
            "sweep_model": es_sweep_model,
            "validation": es_validation,
        }
    }