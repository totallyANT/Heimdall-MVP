from pydantic import BaseModel
from typing import Optional

class IntercomRequest(BaseModel):
    flatNo: str
    requestedBy: str
    call_id: Optional[str] = None