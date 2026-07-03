from pydantic import BaseModel

class DeliveryEntry(BaseModel):
    delivery_id: str
    