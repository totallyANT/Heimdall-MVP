from pydantic import BaseModel
from typing import Optional

class AlertAction(BaseModel):
    alertId: str
    guardId: str
    decision: str      # CONFIRMED or DISMISSED
    action: Optional[str] = None
    reason: str