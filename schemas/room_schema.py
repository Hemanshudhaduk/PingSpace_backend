# schemas/room_schema.py
from pydantic import BaseModel

class RoomCreate(BaseModel):
    name: str
    description: str | None = ""
    server_id: str
    visibility: str = "public"

class RoomUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    visibility: str | None = None

class RoomResponse(BaseModel):
    id: str
    name: str
    description: str | None
    server_id: str
    visibility: str

    class Config:
        from_attributes = True
