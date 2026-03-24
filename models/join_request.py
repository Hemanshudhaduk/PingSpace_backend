from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid
from datetime import datetime

class JoinRequest(Base):
    __tablename__ = 'join_request'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid1()))
    user_id = Column(String, ForeignKey('user.id'), nullable=False)
    sender_user_id = Column(String, ForeignKey('user.id'), nullable=False)
    server_id = Column(String, ForeignKey('server.id'), nullable=False)
    status = Column(String, default='pending', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship('User', foreign_keys=[user_id])
    sender = relationship('User', foreign_keys=[sender_user_id])
    server = relationship('Server')