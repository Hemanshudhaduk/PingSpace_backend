from sqlalchemy import Column, String, Integer, ForeignKey, Index
from database import Base
import uuid

class Attachment(Base):
    __tablename__ = 'attachment'

    __table_args__ = (
        Index('ix_attachment_message_id', 'message_id'),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid1()))
    message_id = Column(String, ForeignKey('message.id', ondelete='CASCADE'), nullable=False)
    file_url = Column(String, nullable=False)       # Cloudinary URL
    file_name = Column(String, nullable=False)      # original filename
    file_size = Column(Integer, nullable=False)     # bytes
    mime_type = Column(String, nullable=False)      # image/jpeg, audio/webm, etc
    width = Column(Integer, nullable=True)          # images only
    height = Column(Integer, nullable=True)         # images only
    duration = Column(Integer, nullable=True)       # audio/video seconds
    