import uuid
import requests
import base64
import config

YOO_KASSA_API_URL = "https://api.yookassa.ru/v3/payments"
YOOKASSA_SECRET_KEY = config.YOOKASSA_SECRET_KEY
YOO_KASSA_SHOP_ID = config.YOOKASSA_SHOP_ID

def create_payment(amount, description, redirect_uri):
    payment_id = str(uuid.uuid4())
    headers = {
        "Content-Type": "application/json",
        "Idempotence-Key": payment_id,
        "Authorization": f"Basic {base64.b64encode(f'{YOO_KASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}'.encode()).decode()}"
    }
    data = {
        "amount": {
            "value": str(amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": redirect_uri
        },
        "capture": True,
        "description": description
    }
    response = requests.post(YOO_KASSA_API_URL, json=data, headers=headers)
    response_data = response.json()
    return response_data["confirmation"]["confirmation_url"], response_data["id"]

def check_payment_status(payment_id):
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{YOO_KASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}'.encode()).decode()}"
    }
    response = requests.get(f"{YOO_KASSA_API_URL}/{payment_id}", headers=headers)
    response_data = response.json()
    return response_data.get("status"), response_data.get("description")