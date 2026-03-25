# models/server.py
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import uuid
class Server(Base):
    __tablename__ = 'server'

    id = Column(String, primary_key=True , default=lambda: str(uuid.uuid1()))
    name = Column(String, nullable = False)
    admin_id = Column(String, ForeignKey('user.id'))
    admin = relationship('User' , back_populates = 'server')
    room = relationship('Room' , back_populates='server' , cascade="all, delete-orphan")
    users = relationship('ServerUser' ,back_populates='server' ,   cascade="all, delete-orphan",
        passive_deletes=True)

# users = [
#     owner_id,

# ]