from sqlalchemy import Column, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from database import Base
import uuid


class RoomMember(Base):
    __tablename__ = 'room_member'

    __table_args__ = (
        Index('ix_room_member_room_id', 'room_id'),
        Index('ix_room_member_user_id', 'user_id'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid1()))
    room_id = Column(String, ForeignKey('room.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    role = Column(String, nullable=False, default='member')

    room = relationship('Room', back_populates='members')
    user = relationship('User', back_populates='room_memberships')