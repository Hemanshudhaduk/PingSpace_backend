from pydantic import BaseModel
from datetime import datetime
from schemas.user_schema import UserResponse

class JoinRequestCreate(BaseModel):
    server_id: str

class JoinRequestUpdate(BaseModel):
    status: str

class JoinRequestOut(BaseModel):
    id: str
    user_id: str
    server_id: str
    status: str
    created_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True