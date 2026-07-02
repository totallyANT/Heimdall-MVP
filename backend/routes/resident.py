from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import db
from schema import ResidentRequest
from datetime import datetime, timedelta
from bson import ObjectId
from zoneinfo import ZoneInfo
import uuid

router = APIRouter()


# ---------- Models ----------
class VehicleAdd(BaseModel):
    resident_id: str
    plate_number: str


class VehicleRemove(BaseModel):
    resident_id: str
    plate_number: str


def normalize_plate(plate: str):
    return plate.upper().replace(" ", "").replace("-", "")


# ---------- Get Resident Profile ----------
@router.get("/profile/{resident_id}")
def get_resident_profile(resident_id: str):

    resident = db.residents.find_one({
        "id": resident_id
    })

    if not resident:
        raise HTTPException(
            status_code=404,
            detail="Resident not found"
        )

    return {
        "full_name": resident["full_name"],
        "id": resident["id"],
        "flat_number": resident["flat_number"],
        "phone": resident["phone"],
        "badge": resident.get("badge", "Not Assigned"),
        "vehicles": resident.get("vehicles", [])
    }


# ---------- Add Vehicle ----------
@router.post("/add-vehicle")
def add_vehicle(payload: VehicleAdd):

    resident = db.residents.find_one({
        "id": payload.resident_id
    })

    if not resident:
        raise HTTPException(
            status_code=404,
            detail="Resident not found"
        )

    normalized_plate = normalize_plate(payload.plate_number)

    existing_vehicle = db.vehicles.find_one({
        "plate_number": normalized_plate
    })

    if existing_vehicle:
        raise HTTPException(
            status_code=400,
            detail="Vehicle already registered"
        )

    db.vehicles.insert_one({
        "plate_number": normalized_plate,
        "resident_id": payload.resident_id
    })

    db.residents.update_one(
        {"id": payload.resident_id},
        {
            "$push": {
                "vehicles": normalized_plate
            }
        }
    )

    return {
        "message": "Vehicle added successfully",
        "plate_number": normalized_plate
    }


# ---------- Remove Vehicle ----------
@router.delete("/remove-vehicle")
def remove_vehicle(payload: VehicleRemove):

    normalized_plate = normalize_plate(payload.plate_number)

    result = db.vehicles.delete_one({
        "plate_number": normalized_plate,
        "resident_id": payload.resident_id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Vehicle not found"
        )

    db.residents.update_one(
        {"id": payload.resident_id},
        {
            "$pull": {
                "vehicles": normalized_plate
            }
        }
    )

    return {
        "message": "Vehicle removed successfully"
    }


# ---------- Report Lost Card ----------
@router.post("/report-lost-card/{resident_id}")
def report_lost_card(resident_id: str):

    resident = db.residents.find_one({
        "id": resident_id
    })

    if not resident:
        raise HTTPException(
            status_code=404,
            detail="Resident not found"
        )

    current_status = resident.get("card_status", "active")

    if current_status == "blocked":
        raise HTTPException(
            status_code=400,
            detail="Card already blocked"
        )

    db.residents.update_one(
        {"id": resident_id},
        {
            "$set": {
                "card_status": "blocked"
            }
        }
    )

    db.security_alerts.insert_one({
        "type": "lost_card",
        "resident_id": resident_id,
        "badge": resident["badge"],
        "message": "Lost card reported",
        "resolved": False
    })

    return {
        "message": "Card blocked successfully. Security notified."
    }


# ---------- Generate Resident Identities (Admin) ----------


@router.post("/generate-identities")
def generate_identities(data: ResidentRequest):

    existing = db.residents.find_one(
        {
            "flat_number": data.flat_number
        }
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Flat {data.flat_number} is already registered."
        )

    output = []

    for index, badge in enumerate(data.resident_badge_ids, start=1):

        resident = {
            "id": f"RES-{data.flat_number}-{index}",
            "flat_number": data.flat_number,
            "badge": badge,
            "password": "pass123",
            "full_name": None,
            "age": None,
            "phone": None,
            "is_initialized": False,
            "vehicles": [],
            "card_status": "active",
            "trust_score": 100
        }

        db.residents.insert_one(resident)

        output.append({
            "Resident": "Resident",
            "Password": resident["password"],
            "Badge": resident["badge"],
            "ID": resident["id"],
            "Flat": resident["flat_number"]
        })

    return output


@router.get("/announcements")
def get_recent_announcements():

    cutoff = datetime.now() - timedelta(hours=24)

    announcements = db.announcements_collection.find({
        "created_at": {"$gte": cutoff}
    }).sort("created_at", -1).to_list(length=50)

    result = []

    for ann in announcements:
        result.append({
            "title": ann["title"],
            "message": ann["message"],
            "created_at": ann["created_at"]
        })

    return {
        "announcements": result
    }

# ---------- Get Pending Requests ----------


@router.get("/pending-requests/{resident_id}")
def get_pending_requests(resident_id: str):

    resident = db.residents.find_one({
        "id": resident_id
    })

    if not resident:
        raise HTTPException(
            status_code=404,
            detail="Resident not found"
        )

    flat = resident["flat_number"]

    pending_deliveries = []
    delivery_cursor = db.delivery_notifications.find({
        "resident_flat": flat,
        "status": "pending"
    })

    for delivery in delivery_cursor:
        pending_deliveries.append({
            "request_id": str(delivery["_id"]),
            "type": "delivery",
            "delivery_service": delivery["delivery_service"],
            "arrival_window": delivery["arrival_window"]
        })

    pending_visitors = []
    visitor_cursor = db.guest_passes.find({
        "resident_flat": flat,
        "status": "pending"
    })

    for visitor in visitor_cursor:
        pending_visitors.append({
            "request_id": str(visitor["_id"]),
            "type": "visitor",
            "guest_name": visitor["guest_name"],
            "entry_date": visitor["entry_date"],
            "duration_days": visitor["duration_days"]
        })

    return {
        "pending_deliveries": pending_deliveries,
        "pending_visitors": pending_visitors
    }

# ---------- Approve Pending Requests for deliveries ----------


@router.post("/approve-request/{resident_id}/{request_type}/{request_id}")
def approve_request(
    resident_id: str,
    request_type: str,
    request_id: str
):
    resident = db.residents.find_one({"id": resident_id})

    if not resident:
        raise HTTPException(
            status_code=404,
            detail="Resident not found"
        )

    if request_type == "delivery":
        count = db.delivery_notifications.count_documents({
            "delivery_id": {"$ne": None}
        })

        delivery_id = f"DLV-{count + 101}"

        approved_time = datetime.now(
            ZoneInfo("Asia/Kolkata")
        ).strftime("%Y-%m-%d %H:%M:%S IST")

        result = db.delivery_notifications.update_one(
            {
                "_id": ObjectId(request_id),
                "status": "pending"
            },
            {
                "$set": {
                    "delivery_id": delivery_id,
                    "resident_id": resident_id,
                    "status": "active",
                    "approved_time": approved_time
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Already handled"
            )

        return {
            "message": "Delivery approved",
            "delivery_id": delivery_id
        }

    # --------- Approve Pending Requests for visitors ----------
    elif request_type == "visitor":
        count = db.guest_passes.count_documents({
            "passId": {"$ne": None}
        })

        pass_id = f"VIS-{count + 101}"
        token = uuid.uuid4().hex

        result = db.guest_passes.update_one(
            {
                "_id": ObjectId(request_id),
                "status": "pending"
            },
            {
                "$set": {
                    "passId": pass_id,
                    "resident_id": resident_id,
                    "status": "active",
                    "qrData.token": token
                }
            }
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Already handled"
            )

        return {
            "message": "Visitor approved",
            "passId": pass_id,
            "qr_url": f"/qr/{pass_id}"
        }

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid request type"
        )

# ---------- Reject Pending Requests ----------


@router.post("/reject-request/{request_type}/{request_id}")
def reject_request(request_type: str, request_id: str):

    if request_type == "delivery":
        result = db.delivery_notifications.update_one(
            {
                "_id": ObjectId(request_id),
                "status": "pending"
            },
            {
                "$set": {
                    "status": "rejected"
                }
            }
        )

    elif request_type == "visitor":
        result = db.guest_passes.update_one(
            {
                "_id": ObjectId(request_id),
                "status": "pending"
            },
            {
                "$set": {
                    "status": "rejected"
                }
            }
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid request type"
        )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Already handled"
        )

    return {
        "message": "Request rejected"
    }
