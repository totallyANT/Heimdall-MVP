from pydantic import BaseModel

class ThreatAction(BaseModel):
    alertId: str
    guardId: str
    action: str