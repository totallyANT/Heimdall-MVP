from fastapi import APIRouter

import database

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)


@router.get("/resident/{resident_id}")
def resident_profile(resident_id: str):

    return database.get_resident_profile(resident_id)


@router.get("/guard/{guard_id}")
def guard_profile(guard_id: str):

    return database.get_guard_profile(guard_id)


@router.get("/admin/{admin_id}")
def admin_profile(admin_id: str):

    return database.get_admin_profile(admin_id)