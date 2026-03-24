from pydantic import BaseModel
from datetime import datetime
from schemas.user_schema import UserResponse

# Add sender_user_id field
class JoinRequestCreate(BaseModel):
    server_id: str
    sender_user_id: str | None = None

class JoinRequestUpdate(BaseModel):
    status: str

class JoinRequestOut(BaseModel):
    id: str
    user_id: str
    sender_user_id: str | None = None
    server_id: str
    status: str
    created_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True