import secrets
from fastapi import APIRouter
from database import db
from schema import SecurityGuardRequest, ResidentRequest
from utils import generate_password

router = APIRouter(prefix="/admin", tags=["Admin Provisioning Engine"])

import re
from fastapi import APIRouter

@router.post("/generate-security-guards")
def generate_security_guards(data: SecurityGuardRequest):
    guards_to_insert = []
    output = []
    
    last_guard = db.security_guards.find_one({}, sort=[("id", -1)])
    start_num = 101

    if last_guard and "id" in last_guard:
        match = re.search(r'\d+', last_guard["id"])
        if match:
            start_num = max(start_num, int(match.group()) + 1)

    for i in range(data.number_of_new_guards):
        current_num = start_num + i
        guard_id = f"GRD-{current_num}"
        guard = {
            "id": guard_id,
            "password": generate_password(),
            "full_name": None,
            "age": None,
            "phone": "",
            "station": "Gate House Alpha",
            "is_initialized": False,
        }
        guards_to_insert.append(guard)
        output.append({
            "Security": "Security",
            "ID": guard_id,
            "Password": guard["password"],
        })

    if guards_to_insert:
        db.security_guards.insert_many(guards_to_insert)
        
    return output

@router.post("/generate-identities")
def generate_identities(data: ResidentRequest):
    existing = db.residents.find_one({"flat_number": data.flat_number})
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Flat {data.flat_number} is already registered."
        )
        
    residents_to_insert = []
    output = []

    for index, badge in enumerate(data.resident_badge_ids, start=1):
        resident = {
            "id": f"RES-{data.flat_number}-{index}",
            "flat_number": data.flat_number,
            "badge": badge,
            "password": generate_password(),
            "full_name": None,
            "age": None,
            "phone": None,
            "is_initialized": False,
            "vehicles": [],
            "card_status": "active",
            "trust_score": 100
        }
        residents_to_insert.append(resident)
        
        output.append({
            "Resident": "Resident",
            "Password": resident["password"],
            "Badge": resident["badge"],
            "ID": resident["id"],
            "Flat": resident["flat_number"]
        })

    if residents_to_insert:
        db.residents.insert_many(residents_to_insert)

    return output