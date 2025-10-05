"""
Message Log Model - Track all incoming/outgoing messages
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from sqlalchemy.sql import func
from config.database import Base


class MessageLog(Base):
    """Message log table for tracking all WhatsApp messages"""

    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # 'incoming' or 'outgoing'
    message_text = Column(Text)
    is_voice = Column(Boolean, default=False)
    wappi_status = Column(String(50))  # Status from Wappi API
    queue_status = Column(String(50))  # 'queued', 'sent', 'failed'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Create composite index for common queries
    __table_args__ = (
        Index('idx_phone_created', 'phone_number', 'created_at'),
        Index('idx_direction_status', 'direction', 'queue_status'),
    )

    def __repr__(self):
        return f"<MessageLog(id={self.id}, phone={self.phone_number}, direction={self.direction})>"
