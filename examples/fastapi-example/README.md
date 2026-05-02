# Shre SDK FastAPI Example

Working FastAPI backend application demonstrating Shre SDK integration with async event batching.

## Features

- **Async Event Queue**: Events queue in memory, auto-flush every 60s
- **Product API**: List and fetch product details (auto-tracks with events)
- **Order Management**: Create and track orders
- **Event Management**: View queued events, manual flush endpoint

## Running

```bash
pip install -r requirements.txt
python main.py
# Starts on http://localhost:8000
# Docs: http://localhost:8000/docs
```

## API Endpoints

### Products
- `GET /products` — List all products
- `GET /products/{id}` — Get product details

### Orders
- `POST /orders` — Create new order
- `GET /orders/{id}` — Get order status

### Events
- `GET /events` — View queued events
- `POST /events/flush` — Manually flush to Shre

### Health
- `GET /health` — Service health
- `GET /readyz` — Ready check

## How Events Flow

1. **API Call** → Product view, order creation
2. **Event Queue** → Events collected in memory
3. **Auto-Flush** → Every 60s, batch-send to Shre
4. **Manual Flush** → POST /events/flush for immediate send

## Integration Example

```python
from shreai_sdk import ShreSDK, Event

sdk = ShreSDK("dev-tenant-001")

# Send events
response = sdk.send_events_batch([
    Event(
        eventId="evt-123",
        eventName="order_created",
        entityType="order",
        entityId="ord-456",
        metadata={"total": 299.99}
    )
])
```

## Production Checklist

- [ ] Change tenant_id to your workspace ID
- [ ] Update API base_url for staging/prod
- [ ] Implement error retry logic
- [ ] Add database persistence for events
- [ ] Monitor event queue size
- [ ] Set up health monitoring
