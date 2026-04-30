from sqlalchemy import Column , String  , ForeignKey
from database import Base 
from sqlalchemy.orm import relationship
import uuid         
class Room(Base) :
    __tablename__ = 'room'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid1()))
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    visibility = Column(String, nullable=False, default="public")
    server_id = Column(String, ForeignKey('server.id'))
    server = relationship('Server', back_populates='room')
    members = relationship('RoomMember', back_populates='room', cascade="all, delete-orphan")
