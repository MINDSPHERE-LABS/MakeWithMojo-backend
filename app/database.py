import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_helper = Database()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    db_helper.client = AsyncIOMotorClient(settings.MONGODB_URI)
    db_helper.db = db_helper.client[settings.DATABASE_NAME]
    try:
        # 1. Clean up existing duplicate order entries in database (keeps only the first document)
        pipeline = [
            {"$group": {"_id": "$order_id", "ids": {"$push": "$_id"}, "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        duplicates = await db_helper.db.orders.aggregate(pipeline).to_list(length=None)
        
        delete_ids = []
        for doc in duplicates:
            # Keep the first ID, delete the remaining duplicates
            delete_ids.extend(doc["ids"][1:])
            
        if delete_ids:
            logger.info(f"Found existing duplicates. Cleaning up {len(delete_ids)} duplicate order entries...")
            await db_helper.db.orders.delete_many({"_id": {"$in": delete_ids}})
            logger.info("Duplicate orders cleanup completed.")
            
        # 2. Build the unique index on order_id
        await db_helper.db.orders.create_index("order_id", unique=True)
        logger.info("Unique index on orders.order_id verified/created.")
    except Exception as e:
        logger.warning(f"Failed to verify/create unique index on orders.order_id: {e}")
    logger.info("Connected to MongoDB!")

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db_helper.client:
        db_helper.client.close()
    logger.info("MongoDB connection closed!")

def get_database():
    return db_helper.db
