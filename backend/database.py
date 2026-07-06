import os
from datetime import datetime
from zoneinfo import ZoneInfo

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
security_db = client[DB_NAME]

def ist_now():
    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%Y-%m-%d %H:%M:%S IST")


# ==========================================================
# ALERTS
# ==========================================================

def save_alert(alert: dict):
    return db.alerts.insert_one(alert).inserted_id


def get_alert(alert_id):
    return db.alerts.find_one(
        {
            "_id": ObjectId(alert_id)
        }
    )


def update_alert(alert_id, updates: dict):
    db.alerts.update_one(
        {
            "_id": ObjectId(alert_id)
        },
        {
            "$set": updates
        }
    )


# ==========================================================
# ALERT FETCHING
# ==========================================================

def get_admin_alerts():

    alerts = list(

        db.alerts.find(

            {
                "assigned_to": "admin",
                "resolved": False
            }

        ).sort("created_at", -1)

    )

    for alert in alerts:

        alert["_id"] = str(alert["_id"])

        if isinstance(alert.get("created_at"), datetime):
            alert["created_at"] = alert["created_at"].isoformat()

        if isinstance(alert.get("updated_at"), datetime):
            alert["updated_at"] = alert["updated_at"].isoformat()

    return alerts


def get_guard_alerts(guard_id):

    alerts = list(

        db.alerts.find(

            {
                "assigned_to": "guard",
                "assigned_guard": guard_id,
                "resolved": False
            }

        ).sort("created_at", -1)

    )

    for alert in alerts:

        alert["_id"] = str(alert["_id"])

        if isinstance(alert.get("created_at"), datetime):
            alert["created_at"] = alert["created_at"].isoformat()

        if isinstance(alert.get("updated_at"), datetime):
            alert["updated_at"] = alert["updated_at"].isoformat()

    return alerts
    


def get_resident_alerts(resident_id):

    alerts = list(

        db.alerts.find(

            {
                "assigned_to": "resident",
                "resident_id": resident_id,
                "resolved": False
            }

        ).sort("created_at", -1)

    )

    for alert in alerts:

        alert["_id"] = str(alert["_id"])


    return alerts


# ==========================================================
# ALERT ACTIONS
# ==========================================================

def assign_guard(alert_id, guard_id):



    result = db.alerts.update_one(

        {
            "_id": ObjectId(alert_id)
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


    updated = db.alerts.find_one(
        {
            "_id": ObjectId(alert_id)
        }
    )


def dismiss_alert(alert_id, feedback):

    db.alerts.update_one(

        {
            "_id": ObjectId(alert_id)
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

    db.alerts.update_one(

        {
            "_id": ObjectId(alert_id)
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


# ==========================================================
# PROFILE HELPERS
# ==========================================================

def get_guard_profile(guard_id):

    return db.security_guards.find_one(

        {
            "id": guard_id
        },

        {
            "_id": 0
        }

    )


def get_admin_profile(admin_id):

    return db.admins.find_one(

        {
            "id": admin_id
        },

        {
            "_id": 0
        }

    )


def get_resident_profile(resident_id):

    return db.residents.find_one(

        {
            "id": resident_id
        },

        {
            "_id": 0
        }

    )


# ==========================================================
# GUARDS
# ==========================================================

def get_all_guards():

    return list(

        db.security_guards.find(

            {},

            {
                "_id": 0
            }

        )

    )