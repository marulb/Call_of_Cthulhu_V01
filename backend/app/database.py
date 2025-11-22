"""
Database configuration and connection management for MongoDB.
Uses Motor for async MongoDB operations.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

# MongoDB connection URLs from environment
MONGODB_SYSTEM_URL = os.getenv("MONGODB_SYSTEM_URL", "mongodb://localhost:27017/call_of_cthulhu_system")
MONGODB_GAMERECORDS_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/call_of_cthulhu_gamerecords")

# Global clients
system_client: Optional[AsyncIOMotorClient] = None
gamerecords_client: Optional[AsyncIOMotorClient] = None


async def connect_to_mongo():
    """Establish connections to both MongoDB databases."""
    global system_client, gamerecords_client

    # Connect to system database (AI knowledge base)
    system_client = AsyncIOMotorClient(MONGODB_SYSTEM_URL)

    # Connect to gamerecords database (player data)
    gamerecords_client = AsyncIOMotorClient(MONGODB_GAMERECORDS_URL)

    print("Connected to MongoDB databases")


async def close_mongo_connection():
    """Close all MongoDB connections."""
    global system_client, gamerecords_client

    if system_client:
        system_client.close()
    if gamerecords_client:
        gamerecords_client.close()

    print("Closed MongoDB connections")


def get_system_db():
    """Get system database instance."""
    return system_client.get_default_database()


def get_gamerecords_db():
    """Get gamerecords database instance."""
    return gamerecords_client.get_default_database()
