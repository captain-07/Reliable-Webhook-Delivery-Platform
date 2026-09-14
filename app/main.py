# app/main.py
from fastapi import FastAPI
from app.api import events, subscriptions

app = FastAPI(title="Webhook Delivery Platform")

app.include_router(events.router, tags=["events"])
app.include_router(subscriptions.router, tags=["subscriptions"])

@app.get("/health")
def health_check():
    return {"status": "ok"}