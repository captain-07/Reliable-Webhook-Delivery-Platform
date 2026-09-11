# app/services/delivery.py
import httpx
from app.services.signing import sign_payload

async def send_webhook(target_url: str, payload: dict, secret: str) -> httpx.Response:
    signature = sign_payload(payload, secret)
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": str(int(__import__("time").time())),
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.post(target_url, json=payload, headers=headers)