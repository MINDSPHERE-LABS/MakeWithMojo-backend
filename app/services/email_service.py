import os
import time
import smtplib
import logging
from email.message import EmailMessage
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger("makewithmojo.email")

class EmailService:
    def __init__(self):
        pass

    @property
    def smtp_server(self) -> str:
        return os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()

    @property
    def smtp_port(self) -> int:
        try:
            return int(os.getenv("SMTP_PORT", "587").strip())
        except ValueError:
            return 587

    @property
    def smtp_username(self) -> str:
        return os.getenv("SMTP_USERNAME", "infomakewithmojo@gmail.com").strip()

    @property
    def smtp_password(self) -> str:
        return os.getenv("SMTP_PASSWORD", "").strip()

    @property
    def sender_email(self) -> str:
        return os.getenv("SENDER_EMAIL", "infomakewithmojo@gmail.com").strip()

    @property
    def sender_name(self) -> str:
        return os.getenv("SENDER_NAME", "MakeWithMojo").strip()

    def is_configured(self) -> bool:
        load_dotenv()
        has_pass = bool(self.smtp_password)
        has_user = bool(self.smtp_username)
        if not (has_pass and has_user):
            logger.warning("[EMAIL SERVICE] SMTP_PASSWORD or SMTP_USERNAME is missing in .env")
            return False
        return True

    def generate_plain_text(self, order: Dict[str, Any]) -> str:
        order_id = order.get("order_id") or order.get("_id") or "N/A"
        customer_name = order.get("name") or "Valued Customer"
        grand_total = float(order.get("grand_total") or 0.0)
        items = order.get("items") or []

        text = f"Hi {customer_name},\n\n"
        text += f"Thank you for your order #{order_id} at MakeWithMojo!\n\n"
        text += "ORDER SUMMARY:\n"
        for item in items:
            title = item.get("title") or "Item"
            qty = item.get("quantity") or 1
            price = float(item.get("price") or 0.0)
            text += f"- {title} x{qty} @ Rs.{price:,.2f}\n"
        text += f"\nGrand Total: Rs.{grand_total:,.2f}\n\n"
        text += "Shipping Address:\n"
        text += f"{order.get('address', '')}\n\n"
        text += "If you have any questions, reply to this email or contact us at infomakewithmojo@gmail.com.\n\n"
        text += "Best regards,\nMakeWithMojo Team"
        return text

    def generate_invoice_html(self, order: Dict[str, Any]) -> str:
        order_id = order.get("order_id") or order.get("_id") or "N/A"
        customer_name = order.get("name") or "Valued Customer"
        customer_email = order.get("email") or ""
        customer_phone = order.get("phone") or ""
        address = order.get("address") or ""
        payment_method = (order.get("payment_method") or "COD").upper()
        payment_status = (order.get("payment_status") or "pending").capitalize()
        order_status = order.get("status") or "Processing"
        created_at = order.get("created_at") or "Today"
        if hasattr(created_at, "strftime"):
            created_at = created_at.strftime("%B %d, %Y - %I:%M %p")
        elif isinstance(created_at, str):
            created_at = created_at.split("T")[0]

        grand_total = float(order.get("grand_total") or 0.0)
        items = order.get("items") or []

        # Generate items rows
        items_rows_html = ""
        items_subtotal = 0.0
        for item in items:
            title = item.get("title") or "Product Item"
            price = float(item.get("price") or 0.0)
            quantity = int(item.get("quantity") or 1)
            selected_size = item.get("selected_size") or ""
            thumbnail = item.get("thumbnail") or ""
            line_total = price * quantity
            items_subtotal += line_total

            size_badge = f'<br><span style="font-size: 11px; color: #64748b; background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">Size: {selected_size}</span>' if selected_size else ""
            img_html = f'<img src="{thumbnail}" alt="{title}" style="width: 48px; height: 48px; object-fit: cover; border-radius: 6px; margin-right: 12px; vertical-align: middle;">' if thumbnail and thumbnail.startswith("http") else ""

            items_rows_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px 8px; font-size: 13px; color: #0f172a;">
                    <div style="display: flex; align-items: center;">
                        {img_html}
                        <div>
                            <strong>{title}</strong>
                            {size_badge}
                        </div>
                    </div>
                </td>
                <td style="padding: 12px 8px; font-size: 13px; color: #475569; text-align: center;">{quantity}</td>
                <td style="padding: 12px 8px; font-size: 13px; color: #475569; text-align: right;">₹{price:,.2f}</td>
                <td style="padding: 12px 8px; font-size: 13px; font-weight: 700; color: #0f172a; text-align: right;">₹{line_total:,.2f}</td>
            </tr>
            """

        delivery_fee = grand_total - items_subtotal if grand_total > items_subtotal else 0.0
        delivery_html = f"₹{delivery_fee:,.2f}" if delivery_fee > 0 else '<span style="color: #16a34a; font-weight: 700;">FREE</span>'

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Order Invoice - MakeWithMojo</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; color: #0f172a;">
            <div style="max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                
                <!-- Header Banner -->
                <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 28px 32px; text-align: center; color: #ffffff;">
                    <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;">MAKEWITHMOJO</h1>
                    <p style="margin: 6px 0 0 0; font-size: 13px; color: #94a3b8; letter-spacing: 0.5px;">TAX INVOICE & ORDER RECEIPT</p>
                </div>

                <!-- Content Area -->
                <div style="padding: 32px;">
                    
                    <!-- Greeting -->
                    <h2 style="margin: 0 0 8px 0; font-size: 18px; color: #0f172a;">Thank you for your order, {customer_name}! 🎉</h2>
                    <p style="margin: 0 0 24px 0; font-size: 14px; color: #475569; line-height: 1.5;">
                        We’re excited to let you know that your order <strong style="color: #0284c7;">#{order_id}</strong> has been confirmed and is being processed by our team.
                    </p>

                    <!-- Order Info Box -->
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px 20px; margin-bottom: 24px;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                            <tr>
                                <td style="padding: 4px 0; color: #64748b; width: 40%;"><strong>Order Number:</strong></td>
                                <td style="padding: 4px 0; color: #0f172a; font-weight: 700;">#{order_id}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;"><strong>Order Date:</strong></td>
                                <td style="padding: 4px 0; color: #0f172a;">{created_at}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;"><strong>Payment Method:</strong></td>
                                <td style="padding: 4px 0; color: #0f172a;">{payment_method}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;"><strong>Payment Status:</strong></td>
                                <td style="padding: 4px 0;">
                                    <span style="background: {'#dcfce7' if payment_status.lower() in ['paid','success'] else '#fef3c7'}; color: {'#166534' if payment_status.lower() in ['paid','success'] else '#92400e'}; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 12px; text-transform: uppercase;">
                                        {payment_status}
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </div>

                    <!-- Customer & Shipping Info -->
                    <div style="display: flex; margin-bottom: 24px; gap: 16px;">
                        <div style="flex: 1; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px;">
                            <h4 style="margin: 0 0 6px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">Shipping Address</h4>
                            <p style="margin: 0; font-size: 13px; color: #0f172a; line-height: 1.4;">
                                <strong>{customer_name}</strong><br>
                                {address}<br>
                                📞 {customer_phone}
                            </p>
                        </div>
                    </div>

                    <!-- Items Table -->
                    <h3 style="margin: 0 0 12px 0; font-size: 15px; color: #0f172a; border-bottom: 2px solid #0f172a; padding-bottom: 6px;">Order Items</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
                        <thead>
                            <tr style="background: #f1f5f9; text-align: left;">
                                <th style="padding: 10px 8px; font-size: 12px; font-weight: 700; color: #475569; border-radius: 4px 0 0 4px;">ITEM</th>
                                <th style="padding: 10px 8px; font-size: 12px; font-weight: 700; color: #475569; text-align: center;">QTY</th>
                                <th style="padding: 10px 8px; font-size: 12px; font-weight: 700; color: #475569; text-align: right;">PRICE</th>
                                <th style="padding: 10px 8px; font-size: 12px; font-weight: 700; color: #475569; text-align: right; border-radius: 0 4px 4px 0;">TOTAL</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_rows_html}
                        </tbody>
                    </table>

                    <!-- Pricing Summary -->
                    <div style="max-width: 260px; margin-left: auto; margin-bottom: 28px;">
                        <table style="width: 100%; font-size: 13px;">
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;">Subtotal:</td>
                                <td style="padding: 4px 0; text-align: right; color: #0f172a; font-weight: 600;">₹{items_subtotal:,.2f}</td>
                            </tr>
                            <tr>
                                <td style="padding: 4px 0; color: #64748b;">Delivery Fee:</td>
                                <td style="padding: 4px 0; text-align: right;">{delivery_html}</td>
                            </tr>
                            <tr style="border-top: 2px solid #0f172a; font-size: 16px;">
                                <td style="padding: 10px 0 0 0; color: #0f172a; font-weight: 800;">Grand Total:</td>
                                <td style="padding: 10px 0 0 0; text-align: right; color: #0284c7; font-weight: 800;">₹{grand_total:,.2f}</td>
                            </tr>
                        </table>
                    </div>

                    <!-- Contact & Support Card -->
                    <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 24px;">
                        <p style="margin: 0; font-size: 13px; color: #1e40af;">
                            Have a question about your order? Email us at <a href="mailto:infomakewithmojo@gmail.com" style="color: #0284c7; font-weight: 700; text-decoration: none;">infomakewithmojo@gmail.com</a>
                        </p>
                    </div>

                </div>

                <!-- Footer -->
                <div style="background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px; text-align: center; font-size: 12px; color: #94a3b8;">
                    <p style="margin: 0 0 4px 0; font-weight: 700; color: #64748b;">MakeWithMojo E-Commerce Store</p>
                    <p style="margin: 0;">Designed & Handcrafted with ❤️ in India</p>
                </div>

            </div>
        </body>
        </html>
        """
        return html_content

    def send_order_invoice(self, order: Dict[str, Any]) -> bool:
        recipient_email = order.get("email") or ""
        if not recipient_email or "@" not in recipient_email:
            logger.warning(f"[EMAIL SERVICE] Skipping email dispatch: No valid recipient email found in order {order.get('order_id')}")
            return False

        if not self.is_configured():
            logger.warning("[EMAIL SERVICE] Cannot send email: SMTP credentials not set in .env (SMTP_PASSWORD missing).")
            return False

        order_id = order.get("order_id") or order.get("_id") or "N/A"
        subject = f"Order Confirmation & Receipt #{order_id} - MakeWithMojo"

        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{self.sender_name} <{self.sender_email}>"
            msg["To"] = recipient_email.strip()
            msg["Reply-To"] = self.sender_email
            msg["Message-ID"] = f"<{order_id}.{int(time.time())}@makewithmojo.com>"
            msg["X-Mailer"] = "MakeWithMojo Store Engine"
            msg["Auto-Submitted"] = "auto-generated"

            plain_body = self.generate_plain_text(order)
            html_body = self.generate_invoice_html(order)

            msg.set_content(plain_body)
            msg.add_alternative(html_body, subtype="html")

            logger.info(f"[EMAIL SERVICE] Connecting to {self.smtp_server}:{self.smtp_port} to send invoice to {recipient_email}...")

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"[EMAIL SUCCESS] Successfully sent order invoice email to {recipient_email} for order #{order_id}")
            print(f"\n==================================================")
            print(f"[EMAIL SUCCESS] Invoice sent to: {recipient_email} (Order #{order_id})")
            print(f"==================================================\n")
            return True
        except Exception as e:
            logger.error(f"[EMAIL ERROR] Failed to send invoice email to {recipient_email}: {e}")
            print(f"[EMAIL ERROR] {e}")
            return False

email_service = EmailService()
