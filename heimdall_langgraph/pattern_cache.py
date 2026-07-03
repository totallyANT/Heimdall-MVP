from datetime import datetime, timedelta
import hashlib

CACHE_EXPIRY_MINUTES = 30

_pattern_cache = {}


def _make_key(signal: dict) -> str:
    """
    Generates a deterministic key for similar incidents.
    """

    text = (
        f"{signal['signal_type']}"
        f"{signal.get('gate_id','')}"
        f"{signal.get('context','')}"
    )

    return hashlib.md5(text.encode()).hexdigest()


def get_cached_result(signal: dict):

    key = _make_key(signal)

    if key not in _pattern_cache:
        return None

    entry = _pattern_cache[key]

    if datetime.now() - entry["timestamp"] > timedelta(minutes=CACHE_EXPIRY_MINUTES):
        del _pattern_cache[key]
        return None

    return entry["result"]


def store_result(signal: dict, result: dict):

    key = _make_key(signal)

    _pattern_cache[key] = {

        "timestamp": datetime.now(),

        "result": result

    }