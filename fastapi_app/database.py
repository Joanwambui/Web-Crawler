import os
from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """
    Central configuration class for database connection.
    """
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "books_db")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Create a single global async MongoDB client
_client = AsyncIOMotorClient(settings.MONGODB_URL)
_db = _client[settings.MONGODB_DB_NAME]


def get_db():
    """
    Provides a reference to the MongoDB database.
    Used as a dependency in routes.
    """
    return _db


def get_books_collection():
    """
    Shortcut to the 'books' collection.
    """
    return _db["books"]


def get_changes_collection():
    """
    Shortcut to the 'books_changes' collection.
    """
    return _db["books_changes"]
