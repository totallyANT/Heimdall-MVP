"""
database.py — All data-access logic for Heimdall.

Key additions vs v1:
  • get_resident_full_profile()  — merges CSV static data + MongoDB live trust_score
  • update_trust_score()         — atomically decrements trust_score in MongoDB
                                   (floor 0.0, ceiling 1.0)
  • Trust score is stored on the resident document in the 'residents' collection.
    If the document doesn't have a trust_score field yet it is initialised to 1.0.
"""

import csv
import os
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from pymongo import MongoClient, DESCENDING, ReturnDocument

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV_PATH = os.path.join(_HERE, "..", "heimdall_security_residents_actual.csv")

# ── connection ────────────────────────────────────────────────────────────────
def get_db():
    uri = os.getenv("MONGO_URI")

    if not uri:
        raise EnvironmentError("❌ MONGO_URI not set.")

    db_name = os.getenv("DB_NAME")

    if not db_name:
        raise EnvironmentError("❌ DB_NAME not set.")

    return MongoClient(uri)[db_name]


# ── resident roster ───────────────────────────────────────────────────────────
def load_resident_ids() -> list[str]:
    return ["RES-101", "RES-112"]



def get_resident_full_profile(user_id: str) -> Optional[dict]:

    if not user_id:
        return None

    db = get_db()

    resident = db["residents"].find_one({"id": user_id})

    if resident is None:
        return None

    resident.pop("_id", None)

    resident["trust_score"] = int(
        resident.get("trust_score", 100)
    )

    return resident


# ── trust score mutation ──────────────────────────────────────────────────────
SEVERITY_PENALTY = {
    "High": 10,
    "Medium": 5,
    "Low": 2
}

def update_trust_score(user_id: str, severity: str) -> dict:
    """
    Decrement the resident's trust_score by the severity penalty.
    Floors at 0.
    Returns:
    {
        "user_id": str,
        "old": float,
        "new": float,
        "delta": float
    }
    """

    if not user_id:
        return {}

    penalty = SEVERITY_PENALTY.get(severity, 2)

    db = get_db()

    # Ensure resident exists and initialize trust score if missing
    db["residents"].update_one(
        {"id": user_id},
        {
            "$setOnInsert": {
                "trust_score": 100
            }
        },
        upsert=True,
    )

    # Fetch current trust score
    doc = db["residents"].find_one(
        {"id": user_id},
        {"trust_score": 1}
    )

    old_score = float(doc.get("trust_score", 100))
    new_score = max(0, old_score - penalty)

    # Save updated trust score
    db["residents"].update_one(
        {"id": user_id},
        {
            "$set": {
                "trust_score": new_score,
                "last_updated": datetime.now().isoformat()
            }
        }
    )

    return {
        "user_id": user_id,
        "old": old_score,
        "new": new_score,
        "delta": -penalty
    }

# ── incident persistence ───────────────────────────────────────────────────────
def save_tailgating_incident(signal: dict) -> str:
    doc = {k: v for k, v in signal.items()}
    result = get_db()["Tailgating_incidents"].insert_one(doc)
    return str(result.inserted_id)


def save_forced_open_incident(signal: dict) -> str:
    doc = {k: v for k, v in signal.items()}
    result = get_db()["Door_Forced_Open_Incidents"].insert_one(doc)
    return str(result.inserted_id)


def save_investigation_report(report: dict) -> None:
    get_db()["Investigation_Reports"].insert_one({k: v for k, v in report.items()})


# ── historical context ─────────────────────────────────────────────────────────
def get_recent_anomalies(
    gate_id: str,
    user_id: Optional[str] = None,
    seconds_back: int = 1,
    limit: int = 5,
) -> dict:
    """
    Tailgating + forced-open history for the gate (and optionally user)
    over the last `seconds_back` seconds.  All ObjectIds stripped.
    """
    db = get_db()
    cutoff = (datetime.now() - timedelta(seconds=seconds_back)).isoformat()

    gate_q = {"gate_id": gate_id, "timestamp": {"$gte": cutoff}}
    user_q = {"responsible_user_id": user_id, "timestamp": {"$gte": cutoff}} if user_id else {}

    def _fetch(col, q):
        return [
            {k: v for k, v in d.items() if k != "_id"}
            for d in db[col].find(q, {"_id": 0}).sort("timestamp", DESCENDING).limit(limit)
        ]

    return {
        "lookback_seconds":         seconds_back,
        "tailgating_at_gate":        _fetch("Tailgating_incidents", gate_q),
        "tailgating_by_user":        _fetch("Tailgating_incidents", user_q) if user_id else [],
        "forced_open_at_gate":       _fetch("Door_Forced_Open_Incidents", gate_q),
    }


def get_cross_incident_correlation(incident_timestamp: str, window_seconds: int = 1) -> dict:
    """Any anomaly in either collection within ±window_seconds of the given timestamp."""
    db = get_db()
    try:
        t = datetime.fromisoformat(incident_timestamp)
    except ValueError:
        return {"correlated_tailgating": [], "correlated_forced_open": []}

    lo = (t - timedelta(seconds=window_seconds)).isoformat()
    hi = (t + timedelta(seconds=window_seconds)).isoformat()
    q  = {"timestamp": {"$gte": lo, "$lte": hi}}

    def _fetch(col):
        return [{k: v for k, v in d.items() if k != "_id"} for d in db[col].find(q, {"_id": 0}).limit(5)]

    return {
        "correlated_tailgating":   _fetch("Tailgating_incidents"),
        "correlated_forced_open":  _fetch("Door_Forced_Open_Incidents"),
    }


# ==========================================================
# ALERTS
# ==========================================================

def ist_now():
    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%Y-%m-%d %H:%M:%S IST")


def save_alert(alert: dict):

    result = get_db()["alerts"].insert_one(alert)

    return str(result.inserted_id)


def get_alert(alert_id):

    return get_db()["alerts"].find_one(

        {

            "alert_id": alert_id

        }

    )


def update_alert(alert_id, updates: dict):

    get_db()["alerts"].update_one(

        {

            "alert_id": alert_id

        },

        {

            "$set": updates

        }

    )


def get_all_guards():

    return list(get_db()["security_guards"].find({}, {"_id": 0}))


def assign_guard(alert_id, guard_id):

    get_db()["alerts"].update_one(

        {

            "alert_id": alert_id

        },

        {

            "$set": {

                "assigned_guard": guard_id,

                "assigned_to": "guard",

                "status": "INVESTIGATING",
                "updated_at": ist_now()

            }

        }

    )


def dismiss_alert(alert_id, feedback):

    get_db()["alerts"].update_one(

        {

            "alert_id": alert_id

        },

        {

            "$set": {

                "dismissed": True,
                "resolved": False,
                "status": "DISMISSED",
                "feedback": feedback,
                "updated_at": ist_now()

            }

        }

    )


def resolve_alert(alert_id, feedback):

    get_db()["alerts"].update_one(

        {

            "alert_id": alert_id

        },

        {

            "$set": {

                "resolved": True,
                "dismissed": False,
                "status": "RESOLVED",
                "feedback": feedback,
                "updated_at": ist_now()

            }

        }

    )
