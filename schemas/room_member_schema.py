from pydantic import BaseModel


class RoomMemberAdd(BaseModel):
    user_id: str
    role: str = "member"


class RoomMemberCreate(BaseModel):
    room_id: str
    user_id: str
    role: str = "member"


class RoomMemberUpdate(BaseModel):
    role: str | None = None


class RoomMemberResponse(BaseModel):
    id: str
    room_id: str
    user_id: str
    role: str

    class Config:
        from_attributes = True