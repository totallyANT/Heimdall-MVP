from fastapi import APIRouter
from models.alert_action import AlertAction
from database import security_db

router = APIRouter()


@router.get("/simulate-alert")
def simulate_alert():

    return {
        "alertId": "ALT001",
        "type": "IDENTITY_THEFT_SUSPECT",
        "location": "server_room_door",

        "profile": {
            "residentId": "RES250",
            "name": "Bob Vance",
            "trustScore": 70,
            "pastInfractions": 2
        },

        "locationHistory": {
            "lastLocation": "North Gate",
            "incidentsToday": 0
        },

        "globalSync": {
            "status": "Clear"
        },

        "reason":
        "Tailgating anomaly detected. Subject Bob Vance swiped access card but perimeter cameras detected an unauthorized individual following closely behind."
    }


@router.post("/alert-action")
def alert_action(data: AlertAction):

    record = {
        "alertId": data.alertId,
        "guardId": data.guardId,
        "decision": data.decision,
        "action": data.action,
        "reason": data.reason
    }

    result =  security_db.alert_actions.insert_one(record)

    return {
        "message": "Action recorded successfully",
        "id": str(result.inserted_id)
    }