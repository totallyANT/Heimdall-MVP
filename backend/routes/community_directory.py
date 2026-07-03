from fastapi import APIRouter, HTTPException
from database import db

router = APIRouter()


@router.get("/community-directory")
def get_community_directory():

    residents = list(
        db.residents.find({}, {"_id": 0})
    )

    guards = list(
        db.security_guards.find({}, {"_id": 0})
    )

    community = []

    # Residents
    for resident in residents:
        community.append({
            "id": resident.get("id"),
            "name": resident.get("full_name") or resident.get("id"),
            "role": "Resident",
            "score": resident.get("trust_score", 100),
            "status": "Active",
            "is_initialized": resident.get("is_initialized", False),
            "card_status": resident.get("card_status", "active")
        })

    # Security Guards
    for guard in guards:
        community.append({
            "id": guard.get("id"),
            "name": guard.get("full_name") or guard.get("id"),
            "role": "Security",
            "score": guard.get("trust_score", 100),
            "status": "Active",
            "is_initialized": guard.get("is_initialized", False),
            "card_status": guard.get("card_status", "active")
        })

    return community


# ---------- DELETE RESIDENT ----------
@router.delete("/resident/{resident_id}")
def delete_resident(resident_id: str):

    result = db.residents.delete_one({"id": resident_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Resident not found")

    return {"message": "Deleted"}


@router.delete("/guard/{guard_id}")
def delete_guard(guard_id: str):

    result = db.security_guards.delete_one({"id": guard_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Guard not found")

    return {"message": "Deleted"}