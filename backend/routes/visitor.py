import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException

from database import db
from schema import (
    DeliveryRequest,
    GroupPassRequest,
    GuestPassRequest,
    WorkerPassRequest,
)

router = APIRouter(prefix="/visitor", tags=["Visitor Pass Management"])
local_tz = ZoneInfo("Asia/Kolkata")


@router.post("/guest")
def create_guest_pass(payload: GuestPassRequest):
    resident = db.residents.find_one({"id": payload.resident_id})
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    guest_count = db.guest_passes.count_documents({})
    guest_id = f"VIS-{guest_count + 101}"

    qr_data = {"passId": guest_id, "type": "guest"}
    guest_doc = {
        "passId": guest_id,
        "resident_id": payload.resident_id,
        "resident_flat": resident["flat_number"],
        "guest_name": payload.guest_name,
        "entry_date": payload.entry_date,
        "duration_days": payload.duration_days,
        "status": "active",
        "qrData": qr_data,
    }
    db.guest_passes.insert_one(guest_doc)
    return {
        "message": "Guest pass created successfully",
        "passId": guest_id,
        "qrData": qr_data,
    }


@router.post("/group")
def create_group_pass(payload: GroupPassRequest):
    resident = db.residents.find_one({"id": payload.resident_id})
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    group_count = db.group_passes.count_documents({})
    group_id = f"GRP-{group_count + 101}"

    qr_data = {"passId": group_id, "type": "group"}
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
        "qrData": qr_data,
    }
    db.group_passes.insert_one(group_doc)
    return {
        "message": "Group pass created successfully",
        "passId": group_id,
        "qrData": qr_data,
    }


@router.post("/worker")
def create_worker_pass(payload: WorkerPassRequest):
    resident = db.residents.find_one({"id": payload.resident_id})
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    worker_count = db.worker_passes.count_documents({})
    worker_id = f"WRK-{worker_count + 101}"

    qr_data = {"workerId": worker_id, "type": "worker"}
    worker_doc = {
        "worker_id": worker_id,
        "resident_id": payload.resident_id,
        "resident_flat": resident["flat_number"],
        "worker_name": payload.worker_name,
        "start_time": payload.start_time,
        "end_time": payload.end_time,
        "status": "active",
        "qrData": qr_data,
    }
    db.worker_passes.insert_one(worker_doc)
    return {
        "message": "Worker pass created successfully",
        "worker_id": worker_id,
        "qrData": qr_data,
    }


@router.post("/delivery")
def create_delivery_notification(payload: DeliveryRequest):
    resident = db.residents.find_one({"id": payload.resident_id})
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    valid_windows = ["1hour", "morning", "afternoon", "evening"]
    if payload.arrival_window not in valid_windows:
        raise HTTPException(status_code=400, detail="Invalid arrival window")

    now_local = datetime.now(local_tz)

    if payload.arrival_window == "morning":
        start_time = now_local.replace(hour=8, minute=0, second=0, microsecond=0)
        end_time = now_local.replace(hour=12, minute=0, second=0, microsecond=0)
    elif payload.arrival_window == "afternoon":
        start_time = now_local.replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = now_local.replace(hour=16, minute=0, second=0, microsecond=0)
    elif payload.arrival_window == "evening":
        start_time = now_local.replace(hour=16, minute=0, second=0, microsecond=0)
        end_time = now_local.replace(hour=20, minute=0, second=0, microsecond=0)
    else:
        start_time = now_local
        end_time = now_local + timedelta(hours=1)

    if now_local >= end_time:
        start_time += timedelta(days=1)
        end_time += timedelta(days=1)

    delivery_count = db.delivery_notifications.count_documents({})
    delivery_id = f"DLV-{delivery_count + 101}"

    delivery_doc = {
        "delivery_id": delivery_id,
        "resident_id": payload.resident_id,
        "resident_name": resident.get("full_name") or "Initialized Resident",
        "resident_flat": resident["flat_number"],
        "delivery_service": payload.delivery_service or "Unknown Courier",
        "arrival_window": payload.arrival_window,
        "start_time": start_time,
        "end_time": end_time,
        "approved_time": now_local.strftime("%Y-%m-%d %H:%M:%S IST"),
        "status": "active"
    }
    
    db.delivery_notifications.insert_one(delivery_doc)
    
    return {
        "message": "Security notified successfully",
        "delivery_id": delivery_id
    }