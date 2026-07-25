import asyncio
import dotenv
dotenv.load_dotenv()

from app.database import connect_to_mongo
from app import crud
from app.services.google_sheets_service import google_sheets_service

async def main():
    await connect_to_mongo()
    orders = await crud.get_all_orders()
    users = await crud.get_admin_users_list()
    analytics = await crud.get_admin_analytics()

    print(f"Loaded {len(orders)} orders, {len(users)} users from database.")
    sheet_id = "10oOv-wJI86x_hx36yghbfmv5iJQpjyY48XPzYkry0_Q"
    
    try:
        sh = google_sheets_service.get_spreadsheet(sheet_id)
        print("Spreadsheet opened successfully:", sh)
    except Exception as err:
        print("Exact Error:", err)

    o = google_sheets_service.sync_orders_to_sheet(orders, sheet_id)
    u = google_sheets_service.sync_customers_to_sheet(users, sheet_id)
    a = google_sheets_service.sync_analytics_to_sheet(analytics, sheet_id)

    print("Live Sync Results:", {
        "Orders": o,
        "Customers": u,
        "Analytics": a
    })

if __name__ == "__main__":
    asyncio.run(main())
