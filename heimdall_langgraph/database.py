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
def load_resident_ids(csv_path: str = DEFAULT_CSV_PATH) -> list[str]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Resident CSV not found: {csv_path}")
    ids: list[str] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("status", "").strip().lower() == "active":
                rid = row.get("_id", "").strip()
                if rid:
                    ids.append(rid)
    if not ids:
        raise ValueError("No active residents found in the CSV roster.")
    return ids


def _csv_profile(user_id: str, csv_path: str = DEFAULT_CSV_PATH) -> Optional[dict]:
    """Raw CSV fields for user_id."""
    if not user_id or not os.path.exists(csv_path):
        return None
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("_id", "").strip() == str(user_id).strip():
                return {k.strip(): v.strip() for k, v in row.items()}
    return None


def get_resident_full_profile(user_id: str) -> Optional[dict]:
    """
    Merge CSV static data with the live trust_score from MongoDB.
    Returns None if the resident is not in the CSV.
    Initialises trust_score to 1.0 in MongoDB if the field is missing.
    """
    if not user_id:
        return None

    csv_data = _csv_profile(user_id)
    if csv_data is None:
        return None

    db = get_db()
    mongo_doc = db["residents"].find_one({"_id": user_id}, {"trust_score": 1})

    if mongo_doc is None:
        # resident exists in CSV but not yet in Mongo residents collection — create stub
        db["residents"].update_one(
            {"_id": user_id},
            {"$setOnInsert": {"trust_score": 1.0}},
            upsert=True,
        )
        trust_score = 1.0
    else:
        trust_score = mongo_doc.get("trust_score", 1.0)

    return {**csv_data, "trust_score": round(float(trust_score), 3)}


# ── trust score mutation ──────────────────────────────────────────────────────
SEVERITY_PENALTY = {"High": 0.10, "Medium": 0.05, "Low": 0.02}

def update_trust_score(user_id: str, severity: str) -> dict:
    """
    Decrement the resident's trust_score by the severity penalty.
    Floors at 0.0.  Returns {"old": float, "new": float, "delta": float}.
    """
    if not user_id:
        return {}

    penalty = SEVERITY_PENALTY.get(severity, 0.02)
    db = get_db()

    # Ensure the document exists with a default score
    db["residents"].update_one(
        {"_id": user_id},
        {"$setOnInsert": {"trust_score": 1.0}},
        upsert=True,
    )

    # Fetch current score
    doc = db["residents"].find_one({"_id": user_id}, {"trust_score": 1})
    old_score = round(float(doc.get("trust_score", 1.0)), 3)
    new_score  = round(max(0.0, old_score - penalty), 3)

    db["residents"].update_one(
        {"_id": user_id},
        {"$set": {"trust_score": new_score, "last_updated": datetime.now().isoformat()}},
    )

    return {"user_id": user_id, "old": old_score, "new": new_score, "delta": -round(penalty, 3)}


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
    hours_back: int = 10,
    limit: int = 5,
) -> dict:
    """
    Tailgating + forced-open history for the gate (and optionally user)
    over the last `hours_back` hours.  All ObjectIds stripped.
    """
    db = get_db()
    cutoff = (datetime.now() - timedelta(hours=hours_back)).isoformat()

    gate_q = {"gate_id": gate_id, "timestamp": {"$gte": cutoff}}
    user_q = {"responsible_user_id": user_id, "timestamp": {"$gte": cutoff}} if user_id else {}

    def _fetch(col, q):
        return [
            {k: v for k, v in d.items() if k != "_id"}
            for d in db[col].find(q, {"_id": 0}).sort("timestamp", DESCENDING).limit(limit)
        ]

    return {
        "lookback_hours":            hours_back,
        "tailgating_at_gate":        _fetch("Tailgating_incidents", gate_q),
        "tailgating_by_user":        _fetch("Tailgating_incidents", user_q) if user_id else [],
        "forced_open_at_gate":       _fetch("Door_Forced_Open_Incidents", gate_q),
    }


def get_cross_incident_correlation(incident_timestamp: str, window_minutes: int = 10) -> dict:
    """Any anomaly in either collection within ±window_minutes of the given timestamp."""
    db = get_db()
    try:
        t = datetime.fromisoformat(incident_timestamp)
    except ValueError:
        return {"correlated_tailgating": [], "correlated_forced_open": []}

    lo = (t - timedelta(minutes=window_minutes)).isoformat()
    hi = (t + timedelta(minutes=window_minutes)).isoformat()
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
