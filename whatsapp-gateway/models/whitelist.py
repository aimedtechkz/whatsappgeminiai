"""
Whitelist Model - Store phone numbers to be ignored
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from config.database import Base


class Whitelist(Base):
    """Whitelist table for phone numbers that should be ignored"""

    __tablename__ = "whitelist"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    note = Column(Text, nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Whitelist(phone={self.phone_number}, note={self.note})>"
