from datetime import datetime, timedelta

COOLDOWN_SECONDS = 30

_recent_events = {}


def should_enqueue(signal: dict) -> bool:
    """
    Returns True if this anomaly should be processed.
    Returns False if a similar anomaly was seen recently.
    """

    key = (
        signal["signal_type"],
        signal["gate_id"]
    )

    now = datetime.now()

    if key in _recent_events:

        last_time = _recent_events[key]

        if now - last_time < timedelta(seconds=COOLDOWN_SECONDS):
            return False

    _recent_events[key] = now

    return True