from fastapi import APIRouter, HTTPException
from database import db

router = APIRouter(prefix="/admin/directory", tags=["Community Directory Management"])

@router.get("/community-directory")
def get_community_directory():
    residents = list(db.residents.find({}, {"_id": 0}))
    guards = list(db.security_guards.find({}, {"_id": 0}))
    community = []

    for resident in residents:
        community.append({
            "id": resident.get("id"),
            "name": resident.get("full_name") or resident.get("id"),
            "role": "Resident",
            "score": resident.get("trust_score", 100),
            "status": "Active" if resident.get("is_initialized", False) else "Pending Activation"
        })

    for guard in guards:
        community.append({
            "id": guard.get("id"),
            "name": guard.get("full_name") or guard.get("id"),
            "role": "Security",
            "score": guard.get("trust_score", 100),
            "status": "Active" if guard.get("is_initialized", False) else "Pending Activation"
        })
    return community

@router.delete("/resident/{resident_id}")
def delete_resident(resident_id: str):
    result = db.residents.delete_one({"id": resident_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resident not found")
    return {"message": "Resident account removed successfully"}

@router.delete("/guard/{guard_id}")
def delete_guard(guard_id: str):
    result = db.security_guards.delete_one({"id": guard_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Guard not found")
    return {"message": "Guard account removed successfully"}