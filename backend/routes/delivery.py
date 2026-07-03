from fastapi import APIRouter
from models.delivery import DeliveryEntry
from database import client
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

router = APIRouter()

db = client["heimdall"]


# ---------------------------------------------------
# Get deliveries visible on Security Dashboard
# ---------------------------------------------------
@router.get("/pending")
def get_pending_deliveries():

    now = datetime.now(ZoneInfo("Asia/Kolkata"))

    deliveries = list(
        db.delivery_notifications.find(
            {
                "status": {
                    "$in": [
                        "active",
                        "PASSED_GATE"
                    ]
                }
            },
            {
                "_id": 0
            }
        )
    )

    visible_deliveries = []

    for delivery in deliveries:

        status = delivery["status"]
        window = delivery["arrival_window"].lower()

        visible = False
        expired = False

        # -----------------------------------------
        # Calculate window start and end
        # -----------------------------------------

        if window == "morning":

            start = now.replace(
                hour=8,
                minute=0,
                second=0,
                microsecond=0
            )

            end = now.replace(
                hour=12,
                minute=0,
                second=0,
                microsecond=0
            )

            # If morning already passed today,
            # assume resident meant tomorrow morning
            if now.hour >= 12 and status == "active":
                start += timedelta(days=1)
                end += timedelta(days=1)

        elif window == "afternoon":

            start = now.replace(
                hour=12,
                minute=0,
                second=0,
                microsecond=0
            )

            end = now.replace(
                hour=16,
                minute=0,
                second=0,
                microsecond=0
            )

            if now.hour >= 16 and status == "active":
                start += timedelta(days=1)
                end += timedelta(days=1)

        elif window == "evening":

            start = now.replace(
                hour=16,
                minute=0,
                second=0,
                microsecond=0
            )

            end = now.replace(
                hour=20,
                minute=0,
                second=0,
                microsecond=0
            )

            if now.hour >= 20 and status == "active":
                start += timedelta(days=1)
                end += timedelta(days=1)

        elif window == "1hour":

            approved = datetime.strptime(
                delivery["approved_time"],
                "%Y-%m-%d %H:%M:%S IST"
            ).replace(
                tzinfo=ZoneInfo("Asia/Kolkata")
            )

            start = approved
            end = approved + timedelta(hours=1)

        else:
            continue

        # -----------------------------------------
        # Decide status
        # -----------------------------------------

        # Before window
        if now < start:

            if status == "active":
                visible = False

            elif status == "PASSED_GATE":
                visible = True

        # During window
        elif start <= now < end:

            visible = True

        # After window
        else:

            expired = True

        # -----------------------------------------
        # Expire
        # -----------------------------------------

        if expired:

            db.delivery_notifications.update_one(
                {
                    "delivery_id": delivery["delivery_id"]
                },
                {
                    "$set": {
                        "status": "EXPIRED"
                    }
                }
            )

            continue

        # -----------------------------------------
        # Visible
        # -----------------------------------------

        if visible:

            visible_deliveries.append(delivery)

            
    print("\nReturned Deliveries:")

    for d in visible_deliveries:
        print(
            d["delivery_id"],
            d["delivery_service"],
            d["status"]
        )

    print()

    return visible_deliveries

# ---------------------------------------------------
# Check delivery for flat
# ---------------------------------------------------
@router.get("/check/{flat_no}")
def check_delivery(flat_no: str):

    deliveries = list(
        db.delivery_notifications.find(
            {
                "resident_flat": flat_no,
                "status": "active"
            },
            {
                "_id": 0
            }
        )
    )

    if not deliveries:
        return {
            "message": "No active delivery found"
        }

    return deliveries


# ---------------------------------------------------
# Allow Entry
# ---------------------------------------------------
@router.post("/allow-entry")
def allow_entry(data: DeliveryEntry):

    print("================================")
    print("Delivery ID:", data.delivery_id)

    delivery = db.delivery_notifications.find_one(
        {
            "delivery_id": data.delivery_id
        }
    )

    print("Mongo Delivery:", delivery)

    if not delivery:
        print("NOT FOUND")
        return {"message": "Delivery not found"}

    print("Current Status:", delivery["status"])
    print("Arrival Window:", delivery["arrival_window"])

    result = db.delivery_notifications.update_one(
        {
            "delivery_id": data.delivery_id
        },
        {
            "$set": {
                "status": "PASSED_GATE",
                "gate_entry_time": datetime.now(
                    ZoneInfo("Asia/Kolkata")
                ).strftime("%Y-%m-%d %H:%M:%S IST")
            }
        }
    )

    print("Modified:", result.modified_count)

    return {"message": "Success"}
# ---------------------------------------------------
# Exit Delivery
# ---------------------------------------------------
@router.post("/exit")
def exit_delivery(data: DeliveryEntry):

    delivery = db.delivery_notifications.find_one(
        {
            "delivery_id": data.delivery_id
        }
    )

    if not delivery:

        return {
            "message": "Delivery not found"
        }

    if delivery["status"] != "PASSED_GATE":

        return {
            "message": "Delivery has not entered the gate"
        }

    result = db.delivery_notifications.update_one(
        {
            "delivery_id": data.delivery_id
        },
        {
            "$set": {
                "status": "EXITED",
                "gate_exit_time": datetime.now(
                    ZoneInfo("Asia/Kolkata")
                ).strftime("%Y-%m-%d %H:%M:%S IST")
            }
        }
    )

    if result.modified_count == 0:

        return {
            "message": "Unable to update delivery"
        }

    return {

        "message": "Delivery exited successfully",

        "delivery_id": data.delivery_id,

        "status": "EXITED"
    }