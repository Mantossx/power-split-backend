from pydantic import BaseModel

class ParticipantCreate(BaseModel):
    name: str

class AssignmentCreate(BaseModel):
    participant_id: int
    bill_item_id: int

class BillUpdate(BaseModel):
    tax_service_amount: float
    grand_total: float

class ParticipantResponse(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    class Config:
        from_attributes = True