import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_helper = Database()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB with Motor Async Connection Pooling...")
    db_helper.client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        maxPoolSize=50,
        minPoolSize=5,
        maxIdleTimeMS=45000,
        serverSelectionTimeoutMS=5000
    )
    db_helper.db = db_helper.client[settings.DATABASE_NAME]
    try:
        # 1. Clean up existing duplicate order entries in database
        pipeline = [
            {"$group": {"_id": "$order_id", "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        duplicates = await db_helper.db.orders.aggregate(pipeline).to_list(length=None)
        
        delete_ids = []
        for doc in duplicates:
            delete_ids.extend(doc["ids"][1:])
            
        if delete_ids:
            logger.info(f"Found existing duplicates. Cleaning up {len(delete_ids)} duplicate order entries...")
            await db_helper.db.orders.delete_many({"_id": {"$in": delete_ids}})
            logger.info("Duplicate orders cleanup completed.")
            
        # 2. Build indexes for max performance & fast queries
        # Orders Collection Indexes
        await db_helper.db.orders.create_index("order_id", unique=True)
        await db_helper.db.orders.create_index("payment_status")
        await db_helper.db.orders.create_index("phone")
        await db_helper.db.orders.create_index("user_id")

        # Products Collection Indexes
        await db_helper.db.products.create_index("slug", unique=True)
        await db_helper.db.products.create_index("category")

        # Users Collection Indexes
        await db_helper.db.users.create_index("phone", unique=True)
        await db_helper.db.users.create_index("session_token")

        # OTPs TTL Index (Automatic Expiration)
        await db_helper.db.otps.create_index("expires_at", expireAfterSeconds=0)

        logger.info("MongoDB collection indexes verified & created successfully.")
    except Exception as e:
        logger.warning(f"Index creation note: {e}")
    logger.info("Connected to MongoDB!")

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db_helper.client:
        db_helper.client.close()
    logger.info("MongoDB connection closed!")

def get_database():
    return db_helper.db
