import asyncio
import dotenv
from datetime import datetime
dotenv.load_dotenv()

from app.database import connect_to_mongo, get_database

async def main():
    await connect_to_mongo()
    db = get_database()

    admin_doc = {
        "email": "admin@makewithmojo.com",
        "phone": "9999999999",
        "name": "MakeWithMojo Admin",
        "password": "AdminPassword123!",
        "role": "admin",
        "created_at": datetime.utcnow()
    }

    # Upsert admin user in MongoDB database
    await db.users.update_one(
        {"email": admin_doc["email"]},
        {"$set": admin_doc},
        upsert=True
    )

    print("SUCCESS! Admin user created/updated in MongoDB database.")
    print(f"Login Email: {admin_doc['email']}")
    print(f"Login Phone: {admin_doc['phone']}")
    print(f"Password: {admin_doc['password']}")

if __name__ == "__main__":
    asyncio.run(main())
