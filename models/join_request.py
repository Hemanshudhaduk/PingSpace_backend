from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

class JoinRequest(Base):
    __tablename__ = 'join_request'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid1()))
    user_id = Column(String, ForeignKey('user.id'))
    server_id = Column(String, ForeignKey('server.id'))
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship('User')
    server = relationship('Server')