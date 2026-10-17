from dataclasses import fields, is_dataclass
from enum import Enum
import json
from pathlib import Path
from datetime import date, datetime

REVERSAL_CANDIDATE_LOG = Path("logs/reversal_candidates.jsonl")
ALERTED_CANDIDATE_LOG = Path("logs/alerted_candidates.jsonl")
AUCTION_LOG = Path("logs/auction_status.jsonl")


def serialize_for_log(obj, active=None):
    """Convert Python objects into readable, JSON-compatible data."""

    if active is None:
        active = set()

    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, dict):
        obj_id = id(obj)
        if obj_id in active:
            return "<circular reference>"

        active.add(obj_id)
        try:
            return {
                str(k): serialize_for_log(v, active)
                for k, v in obj.items()
            }
        finally:
            active.remove(obj_id)

    if isinstance(obj, (list, tuple, set)):
        obj_id = id(obj)
        if obj_id in active:
            return "<circular reference>"

        active.add(obj_id)
        try:
            return [
                serialize_for_log(item, active)
                for item in obj
            ]
        finally:
            active.remove(obj_id)

    obj_id = id(obj)
    if obj_id in active:
        return "<circular reference>"

    active.add(obj_id)
    try:
        if is_dataclass(obj) and not isinstance(obj, type):
            return {
                field.name: serialize_for_log(
                    getattr(obj, field.name), active
                )
                for field in fields(obj)
            }

        if hasattr(obj, "__dict__"):
            return {
                key: serialize_for_log(value, active)
                for key, value in vars(obj).items()
                if not key.startswith("_")
            }

        return str(obj)
    finally:
        active.remove(obj_id)

def log_test(
    data
):
    ALERTED_CANDIDATE_LOG.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "data": data
    }

    with ALERTED_CANDIDATE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")

def log_reversal_candidate(
    market_context,
    candidate,
    co_asset_candidate,
    co_asset,
    is_atr_filter,
    is_rejection,
    is_smt,
    weekly_context,
    last_closed_candle,
    newyork_context,
    smt_context,
    reversal_confirmation,
    auction_engine
):
    
    REVERSAL_CANDIDATE_LOG.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "logged_at": last_closed_candle.timestamp,
        "market_context": market_context,
        "candidate": candidate,
        "newyork_context": newyork_context,
        "co_asset_candidate": co_asset_candidate,
        "co_asset": co_asset,
        "is_atr_filter": is_atr_filter,
        "is_rejection": is_rejection,
        "is_smt": is_smt,
        "weekly_context": weekly_context,
        "reversal_confirmation": reversal_confirmation,
        "smt_context": smt_context,
        "auction_engine": auction_engine,
    }
    readable_record = serialize_for_log(record)

    with REVERSAL_CANDIDATE_LOG.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 100 + "\n")
        f.write("REVERSAL CANDIDATE\n")
        f.write("=" * 100 + "\n")
        f.write(json.dumps(
            readable_record,
            indent=2,
            ensure_ascii=False,
        ))
        f.write("\n")


def log_alerted_candidate(
    market_context,
    candidate,
    co_asset_candidate,
    co_asset,
    is_atr_filter,
    is_rejection,
    is_smt,
    weekly_context,
    last_closed_candle,
    newyork_context,
    smt_context,
    reversal_confirmation,
    auction_engine
):
    
    ALERTED_CANDIDATE_LOG.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "logged_at": last_closed_candle.timestamp,
        "market_context": market_context,
        "candidate": candidate,
        "newyork_context": newyork_context,
        "co_asset_candidate": co_asset_candidate,
        "co_asset": co_asset,
        "is_atr_filter": is_atr_filter,
        "is_rejection": is_rejection,
        "is_smt": is_smt,
        "weekly_context": weekly_context,
        "reversal_confirmation": reversal_confirmation,
        "smt_context": smt_context,
        "auction_engine": auction_engine,
    }
    readable_record = serialize_for_log(record)

    with ALERTED_CANDIDATE_LOG.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 100 + "\n")
        f.write("ALERTED CANDIDATE\n")
        f.write("=" * 100 + "\n")
        f.write(json.dumps(
            readable_record,
            indent=2,
            ensure_ascii=False,
        ))
        f.write("\n")

def log_auction_status(
    last_closed_candle,
    smt_context,
    es_auction_summary,
    nq_auction_summary
):
    
    AUCTION_LOG.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "logged_at": last_closed_candle.timestamp,
        # "smt_context": smt_context,
        "es_auction_summary": es_auction_summary,
        "nq_auction_summary": nq_auction_summary,
    }
    readable_record = serialize_for_log(record)

    with AUCTION_LOG.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 100 + "\n")
        f.write("ALERTED CANDIDATE\n")
        f.write("=" * 100 + "\n")
        f.write(json.dumps(
            readable_record,
            indent=2,
            ensure_ascii=False,
        ))
        f.write("\n")