from datetime import datetime
import uuid


def create_scenario(
    scenario: str,
    event_type: str,
    context: str,
    metadata: dict
):
    """
    Returns a normalized scenario object.
    The simulator will later enrich this with
    resident, location, timestamp, weather etc.
    """

    return {

        "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",

        "scenario": scenario,

        "event_type": event_type,

        "context": context,

        "metadata": metadata,

        "generated_at": datetime.utcnow().isoformat()
    }