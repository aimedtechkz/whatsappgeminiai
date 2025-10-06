"""
Database initialization script for WhatsApp Gateway
Creates tables and populates whitelist
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

from config.database import Base, engine, get_db
from models.message_log import MessageLog
from models.whitelist import Whitelist
from loguru import logger


def init_database():
    """Initialize database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.success("✅ Database tables created")


def populate_whitelist():
    """Populate whitelist with default numbers"""
    db = next(get_db())

    try:
        # Default whitelist numbers
        whitelist_numbers = [
            ("77752837306", "Личный номер 1"),
            ("77018855588", "Личный номер 2"),
            ("77088098009", "Личный номер 3"),
            ("77717778111", "Whitelist номер"),
            ("77012201180", "Whitelist номер"),
            ("77012521001", "Whitelist номер"),
            ("77088000322", "Whitelist номер"),
            ("77780308546", "Whitelist номер"),
            ("77774889923", "Whitelist номер"),
            ("77018332761", "Whitelist номер"),
            ("77019990991", "Whitelist номер"),
            ("77006182004", "Whitelist номер"),
            ("77712222272", "Whitelist номер"),
            ("77476989773", "Whitelist номер"),
            ("77079799882", "Whitelist номер"),
            ("7789954081", "Whitelist номер"),
            ("77024020749", "Whitelist номер")
        ]

        for phone, note in whitelist_numbers:
            # Check if exists
            existing = db.query(Whitelist).filter(
                Whitelist.phone_number == phone
            ).first()

            if not existing:
                whitelist_entry = Whitelist(
                    phone_number=phone,
                    note=note
                )
                db.add(whitelist_entry)
                logger.info(f"Added {phone} to whitelist")

        db.commit()
        logger.success("✅ Whitelist populated")

    except Exception as e:
        logger.error(f"Error populating whitelist: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("🚀 Initializing WhatsApp Gateway Database")
    init_database()
    populate_whitelist()
    logger.success("✅ Database initialization complete")
