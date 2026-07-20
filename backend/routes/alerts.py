from fastapi import APIRouter
from schema import AlertAction
import database

router = APIRouter(prefix="/alerts", tags=["Alerts Management Hub"])

@router.get("/admin")
def admin_alerts():
    return database.get_admin_alerts()

@router.get("/guard/{guard_id}")
def guard_alerts(guard_id: str):
    return database.get_guard_alerts(guard_id)

@router.get("/resident/{resident_id}")
def resident_alerts(resident_id: str):
    return database.get_resident_alerts(resident_id)

@router.post("/{alert_id}/dismiss")
def dismiss_alert(alert_id: str, data: AlertAction):
    database.dismiss_alert(alert_id, data.reason)
    return {"message": "Alert dismissed successfully"}

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str, data: AlertAction):
    database.resolve_alert(alert_id, data.reason)
    return {"message": "Alert resolved successfully"}

@router.post("/{alert_id}/assign/{guard_id}")
def assign_guard(alert_id: str, guard_id: str):
    database.assign_guard(alert_id, guard_id)
    return {"message": "Guard assigned successfully"}