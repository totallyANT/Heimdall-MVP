from fastapi import APIRouter, HTTPException
import database

router = APIRouter(prefix="/profile", tags=["User Profile Specifications"])

@router.get("/resident/{resident_id}")
def resident_profile(resident_id: str):
    profile = database.get_resident_profile(resident_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Resident profile not found")
    return profile

@router.get("/guard/{guard_id}")
def guard_profile(guard_id: str):
    profile = database.get_guard_profile(guard_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Guard profile not found")
    return profile

@router.get("/admin/{admin_id}")
def admin_profile(admin_id: str):
    profile = database.get_admin_profile(admin_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Admin profile not found")
    return profile