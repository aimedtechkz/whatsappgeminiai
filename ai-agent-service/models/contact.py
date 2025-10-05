"""
Contact Model - Store contact information and classification
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, Index
from sqlalchemy.sql import func
from config.database import Base


class Contact(Base):
    """Contact table for storing WhatsApp contact information"""

    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    business_name = Column(String(255), nullable=True)

    # Classification fields
    is_client = Column(Boolean, nullable=True, index=True)  # null = unclassified, True = client, False = not client
    classification_confidence = Column(Float, nullable=True)
    classification_reasoning = Column(Text, nullable=True)

    # Timestamps
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Create composite indexes for common queries
    __table_args__ = (
        Index('idx_is_client_updated', 'is_client', 'updated_at'),
    )

    def __repr__(self):
        return f"<Contact(id={self.id}, phone={self.phone_number}, is_client={self.is_client})>"
