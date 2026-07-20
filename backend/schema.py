from typing import List, Optional
from pydantic import BaseModel, Field

# ==========================================================
#  ADMIN & PROVISIONING SCHEMAS
# ==========================================================

class ResidentRequest(BaseModel):
    number_of_residents: int
    flat_number: str
    resident_badge_ids: List[str]

class SecurityGuardRequest(BaseModel):
    number_of_new_guards: int

class AnnouncementRequest(BaseModel):
    title: str
    message: str

# ==========================================================
#  AUTHENTICATION & INITIALIZATION SCHEMAS
# ==========================================================

class ResidentInitialize(BaseModel):
    id: str
    flat_number: str
    temp_passcode: str
    full_name: str
    age: int = Field(..., ge=15, le=120)
    phone: str
    password: str
    confirm_password: str

class ResidentLogin(BaseModel):
    id: str
    password: str

class SecurityInitialize(BaseModel):
    id: str
    temp_passcode: str
    full_name: str
    age: int = Field(..., ge=18, le=120)
    phone: str
    password: str
    confirm_password: str

class SecurityLogin(BaseModel):
    id: str
    password: str

class AdminLogin(BaseModel):
    id: str
    password: str

# ==========================================================
#  VISITOR & PASS GENERATION SCHEMAS
# ==========================================================

class GuestPassRequest(BaseModel):
    resident_id: str
    guest_name: str
    entry_date: str
    duration_days: int = Field(..., ge=1)

class GroupPassRequest(BaseModel):
    resident_id: str
    group_name: str
    entry_date: str
    duration_days: int = Field(..., ge=1)
    visitor_limit: int = Field(..., ge=2)

class WorkerPassRequest(BaseModel):
    resident_id: str
    worker_name: str
    start_time: str
    end_time: str

class DeliveryRequest(BaseModel):
    resident_id: str
    delivery_service: Optional[str] = None
    arrival_window: str

# ==========================================================
#  DELIVERY TRACKING SCHEMAS
# ==========================================================

class DeliveryEntry(BaseModel):
    delivery_id: str

# ==========================================================
#  ALERT & INCIDENT MANAGEMENT SCHEMAS
# ==========================================================

class AlertAction(BaseModel):
    alertId: str
    guardId: str
    decision: str
    action: Optional[str] = None
    reason: str

class ThreatAction(BaseModel):
    alertId: str
    guardId: str
    action: str

# ==========================================================
#  VEHICLE MANAGEMENT SCHEMAS
# ==========================================================
class VehicleAdd(BaseModel):
    resident_id: str
    plate_number: str

class VehicleRemove(BaseModel):
    resident_id: str
    plate_number: str