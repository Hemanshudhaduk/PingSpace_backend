# schemas/message_schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AttachmentResponse(BaseModel):
    file_url: str
    file_name: str
    file_size: int
    mime_type: str
    width:    Optional[int] = None
    height:   Optional[int] = None
    duration: Optional[int] = None

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    room_id: str
    content: str

class MessageResponse(BaseModel):
    id: str
    room_id: str
    sender: str
    content: Optional[str] = None
    type:       str = "text"
    attachment: Optional[AttachmentResponse] = None
    timestamp: datetime 

    class Config:
        from_attributes = True



    