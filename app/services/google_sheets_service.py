import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger("google_sheets_service")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

class GoogleSheetsService:
    def __init__(self):
        self.creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "makewithmojo-04a593bdc598.json")
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
        self.client = None
        self.spreadsheet = None

    def _get_client(self):
        if self.client:
            return self.client

        # Search for credentials JSON file in backend directory
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        creds_path = os.path.join(base_dir, self.creds_file)
        
        if not os.path.exists(creds_path):
            creds_path = self.creds_file

        if not os.path.exists(creds_path):
            logger.warning(f"Google Service Account key file '{self.creds_file}' not found.")
            return None

        try:
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
            self.client = gspread.authorize(creds)
            return self.client
        except Exception as e:
            logger.error(f"Failed to authorize Google Sheets client: {e}")
            return None

    def get_spreadsheet(self, sheet_id: Optional[str] = None):
        target_id = sheet_id or self.sheet_id or os.getenv("GOOGLE_SHEET_ID", "")
        if not target_id:
            return None

        client = self._get_client()
        if not client:
            return None

        try:
            self.spreadsheet = client.open_by_key(target_id)
            return self.spreadsheet
        except Exception as e:
            logger.error(f"Failed to open Google Sheet ID '{target_id}': {e}")
            return None

    def ensure_worksheets(self, spreadsheet=None):
        sh = spreadsheet or self.get_spreadsheet()
        if not sh:
            return False

        try:
            # 1. Orders Sheet Tab
            try:
                sh.worksheet("Orders")
            except gspread.WorksheetNotFound:
                ws_orders = sh.add_worksheet(title="Orders", rows=500, cols=15)
                orders_headers = [
                    "Order ID", "Date", "Customer Name", "Phone", "Email", 
                    "Address", "Items", "Grand Total (₹)", "Payment Method", 
                    "Payment Status", "Order Status", "Tracking ID", "Last Updated"
                ]
                ws_orders.append_row(orders_headers)

            # 2. Customers Sheet Tab
            try:
                sh.worksheet("Customers")
            except gspread.WorksheetNotFound:
                ws_customers = sh.add_worksheet(title="Customers", rows=500, cols=10)
                customers_headers = [
                    "User ID", "Name", "Phone", "Email", "Role", "Total Orders", "Registered Date"
                ]
                ws_customers.append_row(customers_headers)

            # 3. Analytics Sheet Tab
            try:
                sh.worksheet("Analytics")
            except gspread.WorksheetNotFound:
                ws_analytics = sh.add_worksheet(title="Analytics", rows=100, cols=5)
                analytics_headers = ["Metric", "Value", "Description", "Last Updated"]
                ws_analytics.append_row(analytics_headers)

            return True
        except Exception as e:
            logger.error(f"Failed to ensure worksheets: {e}")
            return False

    def sync_orders_to_sheet(self, orders: List[Dict[str, Any]], sheet_id: Optional[str] = None) -> bool:
        sh = self.get_spreadsheet(sheet_id)
        if not sh:
            return False

        self.ensure_worksheets(sh)

        try:
            ws = sh.worksheet("Orders")
            headers = [
                "Order ID", "Date", "Customer Name", "Phone", "Email", 
                "Address", "Items", "Grand Total (₹)", "Payment Method", 
                "Payment Status", "Order Status", "Tracking ID", "Last Updated"
            ]

            rows = [headers]
            for o in orders:
                items_str = ", ".join([it.get("title", "") for it in o.get("items", [])])
                formatted_date = o.get("created_at")
                if isinstance(formatted_date, datetime):
                    formatted_date = formatted_date.strftime("%Y-%m-%d %H:%M")
                elif formatted_date:
                    formatted_date = str(formatted_date)
                else:
                    formatted_date = ""

                last_up = o.get("updated_at")
                if isinstance(last_up, datetime):
                    last_up = last_up.strftime("%Y-%m-%d %H:%M")
                elif last_up:
                    last_up = str(last_up)
                else:
                    last_up = ""

                rows.append([
                    str(o.get("order_id", "")),
                    formatted_date,
                    str(o.get("name", "")),
                    str(o.get("phone", "")),
                    str(o.get("email", "")),
                    str(o.get("address", "")),
                    items_str,
                    float(o.get("grand_total", 0)),
                    str(o.get("payment_method", "")),
                    str(o.get("payment_status", "")),
                    str(o.get("status", "")),
                    str(o.get("tracking_id", "")),
                    last_up
                ])

            ws.clear()
            ws.update(values=rows, range_name="A1")
            logger.info(f"Successfully synced {len(orders)} orders to Google Sheet")
            return True
        except Exception as e:
            logger.error(f"Error syncing orders to Google Sheet: {e}")
            return False

    def sync_customers_to_sheet(self, users: List[Dict[str, Any]], sheet_id: Optional[str] = None) -> bool:
        sh = self.get_spreadsheet(sheet_id)
        if not sh:
            return False

        self.ensure_worksheets(sh)

        try:
            ws = sh.worksheet("Customers")
            headers = ["User ID", "Name", "Phone", "Email", "Role", "Total Orders", "Registered Date"]

            rows = [headers]
            for u in users:
                c_date = u.get("created_at")
                if isinstance(c_date, datetime):
                    c_date = c_date.strftime("%Y-%m-%d %H:%M")
                elif c_date:
                    c_date = str(c_date)
                else:
                    c_date = ""

                rows.append([
                    str(u.get("id", u.get("_id", ""))),
                    str(u.get("name", "Guest")),
                    str(u.get("phone", "")),
                    str(u.get("email", "")),
                    str(u.get("role", "customer")),
                    int(u.get("total_orders", 0)),
                    c_date
                ])

            ws.clear()
            ws.update(values=rows, range_name="A1")
            logger.info(f"Successfully synced {len(users)} customers to Google Sheet")
            return True
        except Exception as e:
            logger.error(f"Error syncing customers to Google Sheet: {e}")
            return False

    def sync_analytics_to_sheet(self, analytics: Dict[str, Any], sheet_id: Optional[str] = None) -> bool:
        sh = self.get_spreadsheet(sheet_id)
        if not sh:
            return False

        self.ensure_worksheets(sh)

        try:
            ws = sh.worksheet("Analytics")
            headers = ["Metric", "Value", "Description", "Last Updated"]
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            rows = [
                headers,
                ["Monthly Revenue", f"₹{(analytics.get('monthly_revenue') or 0):,.2f}", "Earnings for current calendar month", now_str],
                ["Financial Year (FY) Revenue", f"₹{(analytics.get('fy_revenue') or 0):,.2f}", analytics.get("financial_year_label", "Current FY"), now_str],
                ["Total Registered Users", analytics.get("total_users", 0), "Total registered customer directory count", now_str],
                ["Total Store Orders", analytics.get("total_orders", 0), "Total orders processed on store", now_str]
            ]

            ws.clear()
            ws.update(values=rows, range_name="A1")
            logger.info("Successfully synced Analytics to Google Sheet")
            return True
        except Exception as e:
            logger.error(f"Error syncing Analytics to Google Sheet: {e}")
            return False

google_sheets_service = GoogleSheetsService()
