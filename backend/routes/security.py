from fastapi import APIRouter, HTTPException
from schema import AlertAction
from database import db
from bson import ObjectId

router = APIRouter(prefix="/security", tags=["Guard Action Logs"])

@router.post("/alert-action")
def log_alert_action(data: AlertAction):
    record = {
        "alertId": data.alertId,
        "guardId": data.guardId,
        "decision": data.decision,
        "action": data.action,
        "reason": data.reason
    }
    result = db.alert_actions.insert_one(record)

    if data.decision == "RESOLVE":
        db.alerts.update_one(
            {"_id": ObjectId(data.alertId)},
            {"$set": {
                "resolved": True,
                "dismissed": False,
                "status": "RESOLVED"
            }}
        )
    elif data.decision == "DISMISS":
        db.alerts.update_one(
            {"_id": ObjectId(data.alertId)},
            {"$set": {
                "resolved": False,
                "dismissed": True,
                "status": "DISMISSED"
            }}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid decision type action command")

    return {
        "message": f"Alert state updated to {data.decision} successfully",
        "log_id": str(result.inserted_id)
    }