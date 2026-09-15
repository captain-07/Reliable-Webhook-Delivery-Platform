# app/main.py
from fastapi import FastAPI
from app.api import events, subscriptions, deliveries
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.rate_limit import limiter

app = FastAPI(title="Webhook Delivery Platform")

app.include_router(events.router, tags=["events"])
app.include_router(subscriptions.router, tags=["subscriptions"])
app.include_router(deliveries.router, tags=["deliveries"])


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/health")
def health_check():
    return {"status": "ok"}