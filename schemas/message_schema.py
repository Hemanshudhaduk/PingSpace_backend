# schemas/message_schema.py
from pydantic import BaseModel , Field
from datetime import datetime

class MessageCreate(BaseModel):
    room_id: str
    content: str

class MessageResponse(BaseModel):
    id: str
    room_id: str
    sender: str
    content: str
    timestamp: datetime 

    class Config:
        from_attributes = True
        # populate_by_name = True

    