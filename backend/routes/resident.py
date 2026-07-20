from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from database import db
from schema import VehicleAdd, VehicleRemove

router = APIRouter(prefix="/resident", tags=["Resident Dashboard Operations"])


def normalize_plate(plate: str) -> str:
    return plate.upper().replace(" ", "").replace("-", "")


@router.get("/profile/{resident_id}")
def get_resident_profile(resident_id: str):
    resident = db.residents.find_one({"id": resident_id})
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    
    return {
        "full_name": resident.get("full_name"),
        "id": resident.get("id"),
        "flat_number": resident.get("flat_number"),
        "phone": resident.get("phone"),
        "badge": resident.get("badge", "Not Assigned"),
        "vehicles": resident.get("vehicles", [])
    }


@router.post("/add-vehicle")
def add_vehicle(payload: VehicleAdd):
    resident = db.residents.find_one({"id": payload.resident_id})
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
        
    normalized_plate = normalize_plate(payload.plate_number)
    
    existing_vehicle = db.vehicles.find_one({"plate_number": normalized_plate})
    if existing_vehicle:
        raise HTTPException(status_code=400, detail="Vehicle already registered")
        
    # Link vehicle in the master vehicles collection
    db.vehicles.insert_one({
        "plate_number": normalized_plate,
        "resident_id": payload.resident_id
    })
    
    db.residents.update_one(
        {"id": payload.resident_id},
        {"$push": {"vehicles": normalized_plate}}
    )
    
    return {
        "message": "Vehicle added successfully",
        "plate_number": normalized_plate
    }


@router.delete("/remove-vehicle")
def remove_vehicle(payload: VehicleRemove):
    normalized_plate = normalize_plate(payload.plate_number)
    
    result = db.vehicles.delete_one({
        "plate_number": normalized_plate,
        "resident_id": payload.resident_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    db.residents.update_one(
        {"id": payload.resident_id},
        {"$pull": {"vehicles": normalized_plate}}
    )
    
    return {"message": "Vehicle removed successfully"}


@router.get("/announcements")
def get_recent_announcements():
    cutoff = datetime.now() - timedelta(hours=24)
    announcements = (
        db.announcements_collection.find({"created_at": {"$gte": cutoff}})
        .sort("created_at", -1)
        .to_list(length=50)
    )

    result = []
    for ann in announcements:
        result.append(
            {
                "title": ann["title"],
                "message": ann["message"],
                "created_at": ann["created_at"].isoformat()
                if isinstance(ann["created_at"], datetime)
                else str(ann["created_at"]),
            }
        )
    return {"announcements": result}