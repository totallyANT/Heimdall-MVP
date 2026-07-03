from pydantic import BaseModel
from typing import List


class ResidentRequest(BaseModel):
    number_of_residents: int
    flat_number: str
    resident_badge_ids: List[str]


class SecurityGuardRequest(BaseModel):
    number_of_new_guards: int


class AnnouncementRequest(BaseModel):
    title: str
    message: str