import requests

token = "GU7FfUe302YOPaPT8zfg9ehlf0ozLx9Pb3ZAGhIEXNBMPxprKm91674VndSThlfKfdk1r8CXM9WTrZCoG7HFP1bSJKPYJnuKqOU02hmnwNiaN38ZAWVfdZCrhZAIHgAq7oNsQZDZD"
waba_id = "1061621876218463"

url = f"https://graph.facebook.com/v25.0/{waba_id}/message_templates"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

payload = {
    "name": "makewithmojo_otp_v1",
    "category": "UTILITY",
    "allow_category_change": True,
    "language": "en_US",
    "components": [
        {
            "type": "BODY",
            "text": "Your MakeWithMojo security code is {{1}}. Valid for 2 minutes. Do not share this code.",
            "example": {
                "body_text": [["123456"]]
            }
        }
    ]
}

res = requests.post(url, headers=headers, json=payload)
print("Status Code:", res.status_code)
print("Response:", res.json())
