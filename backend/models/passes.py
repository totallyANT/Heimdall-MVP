from pydantic import BaseModel, Field


class GuestPassRequest(BaseModel):
    resident_id: str
    guest_name: str
    entry_date: str
    duration_days: int = Field(..., ge=1)
