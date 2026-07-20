from fastapi import APIRouter, HTTPException
from schema import DeliveryEntry
from database import client
from datetime import datetime
from zoneinfo import ZoneInfo

router = APIRouter(prefix="/guard/delivery", tags=["Guard Delivery Control"])
db = client["heimdall"]
local_tz = ZoneInfo("Asia/Kolkata")

def get_local_now_str():
    return datetime.now(local_tz).strftime("%Y-%m-%d %H:%M:%S IST")

@router.get("/pending")
def get_pending_deliveries():
    now_local = datetime.now(local_tz)

    db.delivery_notifications.update_many(
        {
            "status": "active",
            "end_time": {"$lt": now_local}
        },
        {"$set": {"status": "EXPIRED"}}
    )
    visible_deliveries = list(
        db.delivery_notifications.find(
            {
                "$or": [
                    {"status": "active"},
                    {"status": "PASSED_GATE"}
                ]
            },
            {"_id": 0}
        )
    )
    return visible_deliveries

@router.post("/allow-entry")
def allow_entry(data: DeliveryEntry):
    result = db.delivery_notifications.update_one(
        {"delivery_id": data.delivery_id, "status": "active"},
        {
            "$set": {
                "status": "PASSED_GATE",
                "gate_entry_time": get_local_now_str()
            }
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Active delivery not found")
    return {"message": "Success"}

@router.post("/exit")
def exit_delivery(data: DeliveryEntry):
    result = db.delivery_notifications.update_one(
        {"delivery_id": data.delivery_id, "status": "PASSED_GATE"},
        {
            "$set": {
                "status": "EXITED",
                "gate_exit_time": get_local_now_str()
            }
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Delivery not found or hasn't entered gate")
    return {"message": "Success"}