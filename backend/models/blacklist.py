from pydantic import BaseModel

class BlacklistRequest(BaseModel):
    alertId: str
    id: str
    name: str
    reason: str
    requestedBy: str