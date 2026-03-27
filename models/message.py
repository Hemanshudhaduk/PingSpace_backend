from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from database import Base
from datetime import datetime, timezone
import uuid

class Message(Base):
    __tablename__ = 'message'

    __table_args__ = (
        Index('ix_message_room_id_timestamp', 'room_id', 'timestamp'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid1()))
    sender = Column(String, nullable=False)
    room_id = Column(String, ForeignKey('room.id'), nullable=False)
    content = Column(String, nullable=True)          # ✅ nullable — media msgs have no text
    type = Column(String, default='text')            # ✅ text | image | file | voice | video
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))