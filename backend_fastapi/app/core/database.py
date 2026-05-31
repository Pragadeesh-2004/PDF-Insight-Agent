"""
MongoDB connection and database utilities
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global database instance
db_client = None
db = None


async def connect_to_mongo():
    """
    Create connection to MongoDB Atlas
    """
    global db_client, db
    
    try:
        logger.info("🔌 Connecting to MongoDB Atlas...")
        db_client = AsyncIOMotorClient(settings.MONGODB_URI)
        
        # Test connection
        await db_client.admin.command('ping')
        
        db = db_client[settings.MONGODB_DATABASE]
        logger.info("✅ Connected to MongoDB Atlas successfully")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """
    Close MongoDB connection
    """
    global db_client
    if db_client:
        logger.info("🔌 Closing MongoDB connection...")
        db_client.close()
        logger.info("✅ MongoDB connection closed")


async def create_indexes():
    """
    Create necessary MongoDB indexes for optimal performance
    NOTE: Do NOT create a unique index on 'sessionId' - use '_id' as the primary key
    """
    try:
        logger.info("📑 Creating MongoDB indexes...")
        
        # Sessions collection - use _id as primary key (no sessionId field)
        sessions_collection = db[settings.MONGODB_SESSIONS_COLLECTION]
        
        # Create TTL index for automatic session expiration
        await sessions_collection.create_index(
            "expires_at",
            expireAfterSeconds=0  # Document will be deleted when expires_at time is reached
        )
        logger.info("✅ Created TTL index on sessions (expires_at)")
        
        # Chunks collection indexes
        chunks_collection = db[settings.MONGODB_CHUNKS_COLLECTION]
        
        await chunks_collection.create_index(
            [("sessionId", ASCENDING), ("documentId", ASCENDING)]
        )
        logger.info("✅ Created index: sessionId + documentId on chunks")
        
        await chunks_collection.create_index(
            [("sessionId", ASCENDING), ("chunkIndex", ASCENDING)]
        )
        logger.info("✅ Created index: sessionId + chunkIndex on chunks")
        
        # Documents collection indexes
        documents_collection = db[settings.MONGODB_DOCUMENTS_COLLECTION]
        await documents_collection.create_index(
            [("sessionId", ASCENDING)]
        )
        logger.info("✅ Created index: sessionId on documents")
        
        # Chat history indexes
        chat_history_collection = db[settings.MONGODB_CHAT_HISTORY_COLLECTION]
        await chat_history_collection.create_index(
            [("sessionId", ASCENDING), ("createdAt", DESCENDING)]
        )
        logger.info("✅ Created index: sessionId + createdAt on chat_history")
        
        logger.info("📝 IMPORTANT: If you see 'duplicate key error' on sessionId, run:")
        logger.info("   db.sessions.dropIndex('sessionId_1')")
        logger.info("   This removes the old unique constraint that causes conflicts.")
        
    except Exception as e:
        logger.warning(f"⚠️  Could not create some indexes: {e}")
        # Don't fail if indexes already exist


def get_db():
    """
    Get database instance
    """
    if db is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return db


async def get_collection(collection_name: str):
    """
    Get a collection from the database
    """
    return get_db()[collection_name]
