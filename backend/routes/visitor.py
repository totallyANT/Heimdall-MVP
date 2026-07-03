from fastapi import APIRouter, HTTPException
from database import db
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

router = APIRouter()


# ---------- Models ----------
class GuestPassRequest(BaseModel):
    resident_id: str
    guest_name: str
    entry_date: str
    duration_days: int = Field(..., ge=1)


class GroupPassRequest(BaseModel):
    resident_id: str
    group_name: str
    entry_date: str
    duration_days: int = Field(..., ge=1)
    visitor_limit: int = Field(..., ge=2)


class WorkerPassRequest(BaseModel):
    resident_id: str
    worker_name: str
    start_time: str
    end_time: str


class DeliveryRequest(BaseModel):
    resident_id: str
    delivery_service: str | None = None
    arrival_window: str

# ---------- Guest Pass ----------


@router.post("/guest")
def create_guest_pass(payload: GuestPassRequest):

    resident =  db.residents.find_one({
        "id": payload.resident_id
    })

    if not resident:
        raise HTTPException(
            status_code=404,
            detail="Resident not found"
        )

    guest_count =  db.guest_passes.count_documents({})
    guest_id = f"VIS-{guest_count + 101}"

    qr_data = {
        "passId": guest_id,
        "type": "guest"
    }

    guest_doc = {
        "passId": guest_id,
        "resident_id": payload.resident_id,
        "resident_flat": resident["flat_number"],
        "guest_name": payload.guest_name,
        "entry_date": payload.entry_date,
        "duration_days": payload.duration_days,
        "status": "active",
        "qrData": qr_data
    }

    db.guest_passes.insert_one(guest_doc)

    return {
        "message": "Guest pass created successfully",
        "passId": guest_id,
        "qrData": qr_data
    }


# ---------- Group Pass ----------
@router.post("/group")
async def create_group_pass(payload: GroupPassRequest):

    resident = await db.residents.find_one({
        "id": payload.resident_id
    })

    if not resident:
        raise HTTPException(
            status_code=404,
            detail="Resident not found"
        )

    group_count = await db.group_passes.count_documents({})
    group_id = f"GRP-{group_count + 101}"

    qr_data = {
        "passId": group_id,
        "type": "group"
    }

    group_doc = {
        "passId": group_id,
        "resident_id": payload.resident_id,
        "resident_flat": resident["flat_number"],
        "group_name": payload.group_name,
        "entry_date": payload.entry_date,
        "duration_days": payload.duration_days,
        "visitor_limit": payload.visitor_limit,
        "used_count": 0,
        "status": "active",
        "qrData": qr_data
    }

    await db.group_passes.insert_one(group_doc)

    return {
        "message": "Group pass created successfully",
        "passId": group_id,
        "qrData": qr_data
    }

# ---------- Worker Pass ----------


@router.post("/worker")
async def create_worker_pass(payload: WorkerPassRequest):

    resident = await db.residents.find_one({
        "id": payload.resident_id
    })

    if not resident:
        raise HTTPException(
            status_code=404,
            detail="Resident not found"
        )

    worker_count = await db.worker_passes.count_documents({})
    worker_id = f"WRK-{worker_count + 101}"

    qr_data = {
        "workerId": worker_id,
        "type": "worker"
    }

    worker_doc = {
        "worker_id": worker_id,
        "resident_id": payload.resident_id,
        "resident_flat": resident["flat_number"],
        "worker_name": payload.worker_name,
        "start_time": payload.start_time,
        "end_time": payload.end_time,
        "status": "active",
        "qrData": qr_data
    }

    await db.worker_passes.insert_one(worker_doc)

    return {
        "message": "Worker pass created successfully",
        "worker_id": worker_id,
        "qrData": qr_data
    }

# ---------- Delivery Request ----------


@router.post("/delivery")
def create_delivery_notification(payload: DeliveryRequest):

    resident = db.residents.find_one({
        "id": payload.resident_id
    })

    if not resident:
        raise HTTPException(
            status_code=404,
            detail="Resident not found"
        )

    valid_windows = ["1hour", "morning", "afternoon", "evening"]

    if payload.arrival_window not in valid_windows:
        raise HTTPException(
            status_code=400,
            detail="Invalid arrival window"
        )

    delivery_count = db.delivery_notifications.count_documents({})
    delivery_id = f"DLV-{delivery_count + 101}"

    approved_time = datetime.now(
    ZoneInfo("Asia/Kolkata")
).strftime("%Y-%m-%d %H:%M:%S IST")

    delivery_doc = {
        "delivery_id": delivery_id,
        "resident_id": payload.resident_id,
        "resident_flat": resident["flat_number"],
        "delivery_service": payload.delivery_service or "Unknown",
        "arrival_window": payload.arrival_window,
        "approved_time": approved_time,
        "status": "active"
    }

    db.delivery_notifications.insert_one(delivery_doc)

    return {
        "message": "Security notified successfully",
        "delivery_id": delivery_id
    }
