from pydantic import BaseModel, Field


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
