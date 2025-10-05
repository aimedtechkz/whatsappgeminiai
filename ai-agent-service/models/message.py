"""
Message Model - Store conversation history
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base


class Message(Base):
    """Message table for storing conversation history"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False, index=True)
    phone_number = Column(String(20), nullable=False)
    message_id = Column(String(255), unique=True, nullable=True)
    message_text = Column(Text, nullable=True)
    is_from_bot = Column(Boolean, default=False)
    is_voice = Column(Boolean, default=False)
    voice_transcription = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationship
    contact = relationship("Contact", backref="messages")

    # Create composite indexes for common queries
    __table_args__ = (
        Index('idx_contact_timestamp', 'contact_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, contact_id={self.contact_id}, is_from_bot={self.is_from_bot})>"
