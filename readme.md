# Webhook Delivery Platform

A production-style webhook delivery infrastructure service — built to solve the same reliability problem that Stripe, Svix, Razorpay, and Twilio solve internally: taking an event from a producer and reliably fanning it out to subscriber endpoints, with retries, signing, and full delivery observability.

## Why this exists

Sending webhooks naively (a direct `POST` from your app to a subscriber URL) breaks down fast: subscriber endpoints go down, time out, or return errors, and without retry logic those events are simply lost. This platform decouples **event ingestion** from **event delivery**, so ingestion is fast and reliable while delivery is retried independently, with full audit history of every attempt.

## Architecture

```
Producer                Platform                          Subscriber
   │                        │                                  │
   │  POST /events          │                                  │
   ├───────────────────────►│                                  │
   │  202 Accepted           │ 1. persist Event                │
   │◄───────────────────────┤ 2. enqueue fan-out job           │
   │                        │                                  │
                             ▼
                      Celery: fan_out_event
                             │
                             │ (looks up matching Subscriptions)
                             ▼
                   Celery: deliver_webhook  ──── HMAC-signed POST ────►
                             │                                          │
                             │◄──────────── response ───────────────────┘
                             │
                   success → log SUCCESS
                   failure → log FAILED, retry with exponential backoff + jitter
                   max retries exhausted → log DEAD (dead-letter)
```

The API layer never blocks on delivery. Ingestion writes to Postgres and hands off to Celery immediately, returning `202 Accepted`. All actual HTTP delivery to subscribers happens asynchronously in Celery workers.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| API framework | FastAPI (async) | I/O-bound workload (many outbound HTTP calls) suits async concurrency |
| Database | PostgreSQL | JSONB for flexible event payloads, ARRAY for subscription event-type filters |
| ORM | SQLAlchemy 2.0 (async for API, sync for workers) | Async matches FastAPI's model; Celery workers are sync by design |
| Task queue | Celery + Redis | Industry-standard combination; native exponential backoff + jitter support |
| HTTP client | httpx (async) | Async-native outbound requests from the delivery worker |
| Monitoring | Flower | Live view of task queue, retries, and failures |
| Containerization | Docker, multi-stage build + docker-compose | Small production images; one-command local stack |

## Key design decisions

**UUID primary keys, not auto-increment integers.** Event and delivery IDs are exposed in API responses and to subscribers. Sequential IDs leak volume information and are enumerable; UUIDs aren't.

**One `DeliveryAttempt` row per attempt, not per (event, subscriber) pair.** This is what makes the delivery-logs feature actually useful for debugging — you can see "attempt 1 timed out, attempt 2 succeeded" as a real history, not just a final state.

**Idempotency via `Idempotency-Key` header.** Producers can safely retry the `POST /events` call after a network failure without creating duplicate events — the platform deduplicates on the key and returns the original event.

**Fan-out into independent per-subscriber Celery tasks**, rather than one task looping through all subscribers. One slow or failing subscriber can't block delivery to the others — each delivery is retried and can fail independently.

**HMAC-SHA256 payload signing with a timestamp header.** Subscribers verify the signature using their own copy of the shared secret (never transmitted), and the timestamp lets them reject replayed requests.

**Exponential backoff with jitter**, not fixed-delay retries. Backoff gives a temporarily-down subscriber time to recover; jitter prevents many simultaneously-failed deliveries from retrying in a synchronized burst (the "thundering herd" problem).

**API-key auth, not JWT/OAuth.** Callers here are backend services, not human users — API keys are the correct primitive for service-to-service infra APIs (this mirrors how Stripe, Svix, and Twilio authenticate their APIs).

**Redis-backed rate limiting, not in-memory.** Since Redis is already a dependency, this costs nothing extra and — unlike an in-memory limiter — works correctly if the API is ever scaled to multiple instances.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/events` | Ingest an event; triggers fan-out to matching subscriptions |
| `POST` | `/subscriptions` | Register a subscriber endpoint and the event types it wants |
| `GET` | `/events/{event_id}/deliveries` | Full delivery attempt history for an event, per subscriber |
| `GET` | `/health` | Health check |

All endpoints except `/health` require an `X-API-Key` header.

## Running locally

```bash
# 1. Start the full stack
docker compose up -d

# 2. Run migrations
docker compose exec api alembic upgrade head

# 3. Register a subscriber (use https://webhook.site for a free test URL)
curl -X POST localhost:8000/subscriptions \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "<webhook.site URL>", "secret": "test-secret", "event_types": ["order.created"]}'

# 4. Send an event
curl -X POST localhost:8000/events \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-key-1" \
  -d '{"event_type": "order.created", "data": {"order_id": 1234}}'

# 5. Check delivery status
curl localhost:8000/events/<event_id>/deliveries -H "X-API-Key: <your-api-key>"
```

- API docs: `localhost:8000/docs`
- Task monitoring: `localhost:5555` (Flower)

## Testing

```bash
pytest
```

Tests are targeted rather than exhaustive, prioritizing the logic where a silent bug would be hardest to notice: HMAC signature correctness and idempotency deduplication.

## Possible extensions

- Manual replay of a past event to a subscriber
- Per-subscriber delivery statistics dashboard
- Webhook signature verification helper library for subscribers (like Stripe's SDKs)
- Configurable retry policy per subscription