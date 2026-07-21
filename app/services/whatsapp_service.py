import os
import httpx
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger("whatsapp_service")

class WhatsAppService:
    def __init__(self):
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "1275287995660619")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v25.0")
        self.template_name = os.getenv("WHATSAPP_TEMPLATE_NAME", "jaspers_market_order_confirmation_v1")
        self.template_lang = os.getenv("WHATSAPP_TEMPLATE_LANG", "en_US")
        self.mode = os.getenv("WHATSAPP_MESSAGE_MODE", "template").lower()

    async def send_otp_message(self, phone: str, otp: str) -> Dict[str, Any]:
        """
        Sends OTP message via Meta WhatsApp Cloud API using configured template or text mode.
        """
        if not self.phone_number_id or not self.access_token:
            logger.warning("WhatsApp API credentials missing from environment.")
            return {
                "sent": False,
                "reason": "Missing WHATSAPP_PHONE_NUMBER_ID or WHATSAPP_ACCESS_TOKEN",
                "dev_otp": otp
            }

        clean_phone = "".join(filter(str.isdigit, phone))
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # If template mode is enabled
        if self.mode == "template" and self.template_name:
            if self.template_name == "jaspers_market_plain_text_v1":
                # Meta approved sample template without parameters
                payload = {
                    "messaging_product": "whatsapp",
                    "to": clean_phone,
                    "type": "template",
                    "template": {
                        "name": "jaspers_market_plain_text_v1",
                        "language": { "code": self.template_lang }
                    }
                }
            elif self.template_name == "jaspers_market_order_confirmation_v1":
                # Meta approved sample template with 3 parameters: Name, OTP/Code, Date
                current_date = datetime.now().strftime("%b %d, %Y")
                payload = {
                    "messaging_product": "whatsapp",
                    "to": clean_phone,
                    "type": "template",
                    "template": {
                        "name": "jaspers_market_order_confirmation_v1",
                        "language": { "code": self.template_lang },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    { "type": "text", "text": "MakeWithMojo User" },
                                    { "type": "text", "text": otp },
                                    { "type": "text", "text": current_date }
                                ]
                            }
                        ]
                    }
                }
            elif self.template_name == "hello_world":
                logger.warning("Sending hello_world template (note: has no OTP variables).")
                payload = {
                    "messaging_product": "whatsapp",
                    "to": clean_phone,
                    "type": "template",
                    "template": {
                        "name": "hello_world",
                        "language": { "code": self.template_lang }
                    }
                }
            else:
                # Custom approved OTP template with body parameter {{1}}
                payload = {
                    "messaging_product": "whatsapp",
                    "to": clean_phone,
                    "type": "template",
                    "template": {
                        "name": self.template_name,
                        "language": { "code": self.template_lang },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    { "type": "text", "text": otp }
                                ]
                            }
                        ]
                    }
                }
        else:
            # Send custom OTP text message
            message_body = (
                f"MakeWithMojo Security Code\n\n"
                f"Your OTP code is: {otp}\n\n"
                f"This code will expire in 5 minutes.\n"
                f"Do not share this code with anyone."
            )
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_phone,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message_body
                }
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                resp_data = response.json()
                
                if response.status_code in (200, 201):
                    logger.info(f"WhatsApp OTP dispatched to {clean_phone}")
                    print(f"[WHATSAPP SERVICE] OTP successfully delivered to {clean_phone} via Meta API!")
                    return {
                        "sent": True,
                        "meta_response": resp_data,
                        "dev_otp": otp
                    }
                else:
                    err_detail = resp_data.get("error", {})
                    err_msg = err_detail.get("message", f"HTTP {response.status_code}")
                    err_code = err_detail.get("code")
                    
                    reason_msg = err_msg
                    if err_code == 131047:
                        reason_msg = "Meta 24-hour customer service window expired. Please send a WhatsApp message to the business number first, or configure an approved Meta WhatsApp OTP template."
                    elif err_code == 131030:
                        reason_msg = "Meta Sandbox Mode: Mobile number is not added to recipient list in Meta Developer Portal."
                    
                    logger.error(f"WhatsApp API error ({response.status_code}, code {err_code}): {err_msg}")
                    print(f"[WHATSAPP SERVICE ERROR] Code {err_code} ({response.status_code}): {reason_msg}")
                    return {
                        "sent": False,
                        "status_code": response.status_code,
                        "error_code": err_code,
                        "reason": reason_msg,
                        "meta_response": resp_data,
                        "dev_otp": otp
                    }
        except Exception as e:
            logger.exception("Failed to call Meta WhatsApp API")
            return {
                "sent": False,
                "error": str(e),
                "dev_otp": otp
            }

whatsapp_service = WhatsAppService()


