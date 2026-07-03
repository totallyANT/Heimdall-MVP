from fastapi import APIRouter
from models.blacklist import BlacklistRequest
from database import security_db

router = APIRouter()

@router.post("/request")
def create_blacklist_request(data: BlacklistRequest):

    request_data = data.model_dump()

    request_data["status"] = "PENDING"

    result = security_db.blacklist_requests.insert_one(request_data)

    return {
        "message": "Blacklist request sent successfully",
        "request_id": str(result.inserted_id)
    }