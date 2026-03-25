from database import Base
from sqlalchemy import  String, ForeignKey, Column , Index
from sqlalchemy.orm import relationship
import uuid

class ServerUser(Base):
    __tablename__ = 'server_user'
    id = Column(String , primary_key=True , default = lambda:str(uuid.uuid1()))

    __table_args__ = (
        Index('ix_serveruser_user_id', 'user_id'),       # ✅ speeds up get_servers
        Index('ix_serveruser_server_id', 'server_id'),   # ✅ speeds up membership checks
    )

    server_id = Column(
        String,
        ForeignKey('server.id', ondelete="CASCADE"),
        primary_key=True
    )

    user_id = Column(
        String,
        ForeignKey('user.id', ondelete="CASCADE"),
        primary_key=True
    )

    role = Column(String)

    # relationships
    server = relationship("Server", back_populates="users")
    user = relationship("User", back_populates="servers")
