import asyncio
import dotenv
dotenv.load_dotenv()

from app.database import connect_to_mongo, get_database

async def main():
    await connect_to_mongo()
    db = get_database()
    admins = await db.users.find({"role": "admin"}).to_list(100)
    print(f"Total Admin Users found in MongoDB: {len(admins)}")
    for a in admins:
        print(f" - Email/Phone: {a.get('email') or a.get('phone')} | Name: {a.get('name')} | Password: {a.get('password')}")

if __name__ == "__main__":
    asyncio.run(main())
