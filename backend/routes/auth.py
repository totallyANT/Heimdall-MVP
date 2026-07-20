from fastapi import APIRouter, HTTPException
import bcrypt
from database import db
from schema import (
    ResidentInitialize,
    ResidentLogin,
    SecurityInitialize,
    SecurityLogin,
    AdminLogin
)

router = APIRouter(prefix="/auth", tags=["Unified Authentication Engine"])

@router.post("/initialize")
def initialize_resident(resident: ResidentInitialize):
    if resident.password != resident.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    existing_resident = db.residents.find_one({
        "id": resident.id,
        "flat_number": resident.flat_number,
        "password": resident.temp_passcode
    })

    if not existing_resident:
        raise HTTPException(status_code=401, detail="Invalid ID / flat number / temp passcode")

    if existing_resident.get("is_initialized", False):
        raise HTTPException(status_code=400, detail="Resident already initialized")

    hashed_password = bcrypt.hashpw(resident.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    db.residents.update_one(
        {"id": resident.id},
        {
            "$set": {
                "password": hashed_password,
                "full_name": resident.full_name,
                "age": resident.age,
                "phone": resident.phone,
                "is_initialized": True
            }
        }
    )
    return {"message": "Credentials initialized successfully"}

@router.post("/login")
def login_resident(credentials: ResidentLogin):
    resident = db.residents.find_one({"id": credentials.id})
    if not resident or not resident.get("is_initialized", False):
        raise HTTPException(status_code=401, detail="Invalid credentials or account uninitialized")

    if not bcrypt.checkpw(credentials.password.encode("utf-8"), resident["password"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "resident": {
            "id": resident["id"],
            "full_name": resident["full_name"],
            "flat_number": resident["flat_number"]
        }
    }

@router.post("/security/initialize")
def initialize_security(guard: SecurityInitialize):
    if guard.password != guard.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    existing_guard = db.security_guards.find_one({
        "id": guard.id,
        "password": guard.temp_passcode
    })

    if not existing_guard:
        raise HTTPException(status_code=401, detail="Invalid guard ID / temp passcode")

    if existing_guard.get("is_initialized", False):
        raise HTTPException(status_code=400, detail="Guard already initialized")

    hashed_password = bcrypt.hashpw(guard.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    db.security_guards.update_one(
        {"id": guard.id},
        {
            "$set": {
                "password": hashed_password,
                "full_name": guard.full_name,
                "age": guard.age,
                "phone": guard.phone,
                "is_initialized": True
            }
        }
    )
    return {"message": "Security credentials initialized successfully"}

@router.post("/security/login")
def login_security(credentials: SecurityLogin):
    guard = db.security_guards.find_one({"id": credentials.id})
    if not guard or not guard.get("is_initialized", False):
        raise HTTPException(status_code=401, detail="Invalid credentials or account uninitialized")

    if not bcrypt.checkpw(credentials.password.encode("utf-8"), guard["password"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Security login successful",
        "guard": {"id": guard["id"], "full_name": guard["full_name"]}
    }

@router.post("/admin/login")
def login_admin(credentials: AdminLogin):
    admin = db.admins.find_one({"id": credentials.id})
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    if not bcrypt.checkpw(credentials.password.encode("utf-8"), admin["password"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    return {
        "message": "Admin login successful",
        "admin": {"id": admin["id"], "full_name": admin["full_name"]}
    }