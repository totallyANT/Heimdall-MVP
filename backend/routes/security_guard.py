from fastapi import APIRouter

from schema import SecurityGuardRequest
from database import db

router = APIRouter()


@router.post("/generate-security-guards")
def generate_security_guards(data: SecurityGuardRequest):

    output = []

    for _ in range(data.number_of_new_guards):

        start_id = 101

        # Find the next available ID
        while db.security_guards.find_one({"id": f"GRD-{start_id}"}):
            start_id += 1

        guard = {
            "id": f"GRD-{start_id}",
            "password": "guard123",
            "full_name": None,
            "age": None,
            "phone": "",
            "station": "Gate House Alpha",
            "is_initialized": False
        }

        db.security_guards.insert_one(guard)

        output.append({
            "Security": "Security",
            "ID": guard["id"],
            "Password": guard["password"]
        })

    return output
