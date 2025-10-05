"""
Database initialization script for AI Agent Service
Creates tables
"""
import sys
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Check DATABASE_URL
if not os.getenv("DATABASE_URL"):
    print("❌ ERROR: DATABASE_URL not found in environment variables!")
    print("Please check your .env file exists and contains DATABASE_URL")
    print(f"Current directory: {os.getcwd()}")
    print(f".env exists: {os.path.exists('.env')}")
    sys.exit(1)

print(f"✅ DATABASE_URL loaded: {os.getenv('DATABASE_URL')[:50]}...")

from config.database import Base, engine
from models.contact import Contact
from models.message import Message
from models.follow_up import FollowUp
from models.scheduled_call import ScheduledCall
from loguru import logger


def init_database():
    """Initialize database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.success("✅ Database tables created")


if __name__ == "__main__":
    logger.info("🚀 Initializing AI Agent Service Database")
    init_database()
    logger.success("✅ Database initialization complete")
