# app/services/signing.py
import hmac
import hashlib
import json

def sign_payload(payload: dict, secret: str) -> str:
    """Returns hex HMAC-SHA256 signature of the JSON payload."""
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return signature