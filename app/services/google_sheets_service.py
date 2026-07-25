import os
import json
import base64
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

DEFAULT_SHEET_ID = "10oOv-wJI86x_hx36yghbfmv5iJQpjyY48XPzYkry0_Q"

# Fallback Base64 Encoded Service Account Credentials for Production Server
B64_EMBEDDED_CREDENTIALS = "ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAibWFrZXdpdGhtb2pvIiwKICAicHJpdmF0ZV9rZXlfaWQiOiAiMDRhNTkzYmRjNTk4YTcyNGQyNDU1MGNmMGUwYmRkYjUwZWRhNDExMCIsCiAgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZRSUJBREFOQmdrcWhraUc5dzBCQVFFRkFBU0NCS2N3Z2dTakFnRUFBb0lCQVFERi9KVjRsSGdSb0M5NFxubUxPbzlwMWVXZThydERCZFVrUmFsR25RT3ZyaVhyK1hrYlUxU1hmUHk0a0lTck12WXl2V3Q2RWVWVURUYVhSSVxubXdKR1VyUU5zcHpVVHBOVHBmcTZpYTlBYXhrblZhWGZyUGliYzRoSVFucEsvSDJOekNXYlNGZmJCazB0MWxOVlxuYWhHQ1BWaDNlSVFDd2Q0MXBoTEJtTm5kTDdXRzhZNjJnWWRNM0VSZncvWjl0MDVwcFVKNDZ6U0FMRFpVSUtJOFxuS3N4aDN3L1BKRWo5SFB5RytwZTNXZ1F1USszSWc2QW81YVZ4SU1ER0VobFhoTEk4S00zY0x1WmE2NVhZWmRmTlxuNmlZZ0xqRjc0V1RIenpUNFVlanpWT3VleEljbUZLbUN0MEZmeGJnSEpmT1EzOFQvc1V6cXFPWlluQVhSbzBzUFxuZ1VyQ2k2K1BBZ01CQUFFQ2dnRUFEME1WVXFJL1R6eUY3RW41TDRFelNGNnViVFFLdG1idEZmNXkyYlp5T0prTlxuTStYcmpod0h2R0Q0UTBkZTRMeElXTmoyOXB1ano2aEZhb05vZlh0S25mT3kyenJqYUlOVy9LSTRmRUxGUVo3OFxubG0yRERKaXZYTUtqSXJ5c0FRNUhwOXkveVFhSFZJMDlCMHlSNVBSTnFZZ0V4U0drdTRYOTFDYXdSTGkweVo0YVxucUc3UXNINm1tRENadkxWZ0RvczNwR1N3b291ZDdEMjF6TXMxY3p1cG00RmZDY2dxREVKaERadEdmbktnUkpOUFxuVTROREQ2TlJ2cWx2Y2N3SXIwRVRVNWVnS0xROGxLeHpSTFhEQU9sVnlUODdrUVhrckJ3cmZabXNNVTVic2NPelxub3MvSHphcW9IdG0yM3BkRXBUWEZ4c2tKamJRcmYvRWtlVW0vOE9MaHdRS0JnUURpVGg3MTBOaE1xNmMyWUJkWlxueXkxeXZVZXdRQmM2SElqbGF2T0RYY2VlZXZQMnZodkphaEtMRjJTZHpPU1Nsb2s2TmZCeCtMdVdESEY2SHFXTFxuWFpaV1VscjFNSVJuaTk0NXFFSDlOa3dPbjlNaDFuRzAyb05tRElsaGR0NXEvVGJjQ09BcDJVaTZwYnZpcFd1ZFxuOWlTZ1pFL3lETjRHeTNzL0NGWHpHeUkvbVFLQmdRRGY5elZQcFA0aXU2Y1hhTjVZak43ZTlHQXJ0bkQ3MGFoQlxuUUQxMGVKVkZsdTBaOE51WjhlT1N6Tk1EVURRb1NTcm9CRi9FNWFYdTRwZ29Ta1hqU0xoL1hpK2tVb3U0K2k0NVlqK1NzTDZabTZkcW9HR0tVMXFPM0ROZUN6VisxNEZKZXhqTm15ekwzUGxLR0x0TG5Xb1xuTGkwYXRuaUJad0tCZ0dNUnMvZ0VyMHdSTVNoYXRKNDRsZkxPN2QwNGtYSjlIMmpmZ3k4VkZOaEtGeGNEYm9La1xuRHU0WkZaRUhLMkVJeVpaVUdxaXFMT1NwR2R4T0lrWjZkOS9lT2Jkd3YrWGNrekpHZUd6eklpU2N6djdYTS92cVxuVk8rTnVXNlRiUmNGTnNqb2tjbUFONWlPQ1V4VkFtR3FhYXBWZjdJRTlBV2hlcGpEZTJ6cmlmaXhBb0dBYmMzaVxudWtpWFBHb3FNc1Q4ZGdlaTRVYUl2QVczZ1E2NllqdGZwZkhVcFlpb2VGWmlvc1hseHZONlVCbldWTzQvdHpBUlxuVjFFTUhQMVVZRHliTjJWZ0tNWU93dTlnbVNaZUd0Uk4xWWlnQ1RzK0J5Q3FPSnBvMjZGS3pFd2pNcWFmU04wWlxub2ZNd2NEek1UTlBhQUk1WFhzWitHTFRqUTR2S3JZanVIakdtQlRNQ2dZRUF0QUtYdFgzaStBTzZPd0JFWXMzMVxuN1lCUi9kZUluUXQydUg3S2dKVjBsM2FUajdNVFI4RUMxTjNHbUZVN0VTSjN0bXdHQXhkeXJEY0ZtS2p5OTlLMFxuWmdZV01ZQlBQcGxTUW1ycnFtalZ1NElXNzZwSFFMcWVaSTZNZEhEVzNudFdYQzd1cDhBNWJnNzJtbDlCOXRFeVxuWWhyaEo1V0xrVUM1VFNZMXNvblFkVm89XG4tLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tXG4iLAogICJjbGllbnRfZW1haWwiOiAibWFrZXdpdGhtb2pvLXNoZWV0cy1zeW5jQG1ha2V3aXRobW9qby5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMTQ5NTAzMTgxMjMwMjg4NDI3NTgiLAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIsCiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L21ha2V3aXRobW9qby1zaGVldHMtc3luYyU0MG1ha2V3aXRobW9qby5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsCiAgInVuaXZlcnNlX2RvbWFpbiI6ICJnb29nbGVhcGlzLmNvbSIKfQo="

class GoogleSheetsService:
    def __init__(self):
        self.creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "makewithmojo-04a593bdc598.json")
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID", DEFAULT_SHEET_ID)
        self.client = None
        self.spreadsheet = None

    def _get_client(self):
        if self.client:
            return self.client

        # 1. Check local key file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        creds_path = os.path.join(base_dir, self.creds_file)
        if not os.path.exists(creds_path):
            creds_path = self.creds_file

        if os.path.exists(creds_path):
            try:
                creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
                self.client = gspread.authorize(creds)
                return self.client
            except Exception as e:
                logger.error(f"Failed to auth from JSON file: {e}")

        # 2. Check environment variable GOOGLE_SERVICE_ACCOUNT_JSON
        env_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if env_json:
            try:
                info = json.loads(env_json)
                creds = Credentials.from_service_account_info(info, scopes=SCOPES)
                self.client = gspread.authorize(creds)
                return self.client
            except Exception as e:
                logger.error(f"Failed to auth from GOOGLE_SERVICE_ACCOUNT_JSON: {e}")

        # 3. Fallback to embedded B64 credentials for production
        try:
            raw_json = base64.b64decode(B64_EMBEDDED_CREDENTIALS).decode("utf-8")
            info = json.loads(raw_json)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
            self.client = gspread.authorize(creds)
            return self.client
        except Exception as e:
            logger.error(f"Failed to auth from embedded B64 credentials: {e}")
            return None

    def clean_sheet_id(self, raw_id: str) -> str:
        if not raw_id:
            return ""
        raw_id = raw_id.strip()
        if "docs.google.com/spreadsheets/d/" in raw_id:
            parts = raw_id.split("/d/")
            if len(parts) > 1:
                raw_id = parts[1].split("/")[0].split("?")[0]
        return raw_id.split("/")[0].split("?")[0].strip()

    def get_spreadsheet(self, sheet_id: Optional[str] = None):
        raw = sheet_id or os.getenv("GOOGLE_SHEET_ID") or DEFAULT_SHEET_ID
        target_id = self.clean_sheet_id(raw) or DEFAULT_SHEET_ID
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
            print(f"[GOOGLE SHEETS ERROR] Failed to open Sheet ID '{target_id}': {e}")
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
