from database import Base 
from sqlalchemy import Column  ,ForeignKey ,  String , DateTime , Index
from datetime import datetime
# from sqlalchemy.orm import relationship
import uuid
class Message(Base) :
    __tablename__ = 'message'

    __table_args__ = (
        Index('ix_message_room_id_timestamp', 'room_id', 'timestamp'),  # ✅ speeds up get_history
    )
    id = Column(String , primary_key=True ,  default=lambda: str(uuid.uuid1()))
    sender = Column(String , nullable=False)
    room_id = Column(String, ForeignKey('room.id'), nullable=False)
    content = Column(String , nullable=False)
    timestamp = Column(DateTime , default=datetime.utcnow)