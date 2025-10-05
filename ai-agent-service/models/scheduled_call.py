"""
Scheduled Call Model - Manage scheduled calls
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base


class ScheduledCall(Base):
    """Scheduled calls table for managing call appointments"""

    __tablename__ = "scheduled_calls"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String(50), default='Asia/Almaty', nullable=False)
    status = Column(String(50), default='scheduled', nullable=False)  # 'scheduled', 'completed', 'cancelled'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    contact = relationship("Contact", backref="scheduled_calls")

    # Create index for scheduled calls
    __table_args__ = (
        Index('idx_scheduled_status', 'scheduled_at', 'status'),
    )

    def __repr__(self):
        return f"<ScheduledCall(id={self.id}, contact_id={self.contact_id}, scheduled_at={self.scheduled_at}, status={self.status})>"
