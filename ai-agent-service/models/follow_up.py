"""
Follow Up Model - Manage follow-up sequences
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from config.database import Base


class FollowUp(Base):
    """Follow-up table for managing 5-touch follow-up sequences"""

    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='CASCADE'), nullable=False)
    touch_number = Column(Integer, default=1, nullable=False)  # 1-5
    next_touch_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_touch_at = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False, index=True)
    stop_reason = Column(String(100), nullable=True)  # 'client_responded', 'client_said_yes', 'client_said_no', 'completed_5_touches'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    contact = relationship("Contact", backref="follow_ups")

    # Add constraint for touch_number
    __table_args__ = (
        CheckConstraint('touch_number >= 1 AND touch_number <= 5', name='check_touch_number_range'),
        Index('idx_next_touch_incomplete', 'next_touch_at', 'is_completed'),
    )

    def __repr__(self):
        return f"<FollowUp(id={self.id}, contact_id={self.contact_id}, touch={self.touch_number}, completed={self.is_completed})>"
