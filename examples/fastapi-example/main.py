from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager
import os
import sys
import json
from datetime import datetime
from uuid import uuid4

sys.path.insert(0, '/Users/aibot/Documents/Projects/shreai/aros-developer-portal/sdks/python')

from shreai_sdk import ShreSDK, Event
from shreai_sdk.exceptions import ShreError

app = FastAPI(title="Shre SDK FastAPI Example", version="1.0.0")

# Global SDK instance
sdk = ShreSDK(tenant_id="dev-tenant-001", base_url="https://apiauth.shre.ai")
event_queue = []
background_task = None

async def flush_events_periodically():
    """Flush queued events every 60 seconds"""
    while True:
        await asyncio.sleep(60)
        if event_queue:
            try:
                events = [Event(**e) for e in event_queue.copy()]
                response = sdk.send_events_batch(events)
                event_queue.clear()
                print(f"Flushed {len(events)} events: {response}")
            except ShreError as e:
                print(f"Error flushing events: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown"""
    global background_task
    background_task = asyncio.create_task(flush_events_periodically())
    yield
    background_task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "shre-fastapi-example"}

@app.get("/readyz")
async def readyz():
    """Readiness check"""
    return {"ready": True}

@app.get("/products")
async def list_products():
    """List available products"""
    products = [
        {"id": "1", "name": "Laptop", "price": 999, "stock": 10},
        {"id": "2", "name": "Mouse", "price": 29, "stock": 50},
        {"id": "3", "name": "Keyboard", "price": 79, "stock": 30},
        {"id": "4", "name": "Monitor", "price": 299, "stock": 15},
    ]

    # Track product list view
    queue_event({
        "eventId": str(uuid4()),
        "eventName": "product_list_view",
        "entityType": "page",
        "entityId": "products",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })

    return {"products": products, "count": len(products)}

@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get product details"""
    products = {
        "1": {"id": "1", "name": "Laptop", "price": 999, "stock": 10, "category": "electronics"},
        "2": {"id": "2", "name": "Mouse", "price": 29, "stock": 50, "category": "accessories"},
        "3": {"id": "3", "name": "Keyboard", "price": 79, "stock": 30, "category": "accessories"},
        "4": {"id": "4", "name": "Monitor", "price": 299, "stock": 15, "category": "electronics"},
    }

    product = products.get(product_id)
    if not product:
        return JSONResponse({"error": "not found"}, status_code=404)

    # Track product view
    queue_event({
        "eventId": str(uuid4()),
        "eventName": "product_view",
        "entityType": "product",
        "entityId": product_id,
        "metadata": {
            "name": product["name"],
            "price": product["price"],
            "category": product["category"],
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })

    return product

@app.post("/orders")
async def create_order(order: dict):
    """Create an order"""
    order_id = str(uuid4())

    # Track order creation
    queue_event({
        "eventId": str(uuid4()),
        "eventName": "order_created",
        "entityType": "order",
        "entityId": order_id,
        "metadata": {
            "items": order.get("items", []),
            "total": order.get("total", 0),
            "customer": order.get("customer", ""),
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })

    return {
        "orderId": order_id,
        "status": "created",
        "items": order.get("items", []),
        "total": order.get("total", 0),
    }

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get order status"""
    return {
        "orderId": order_id,
        "status": "pending",
        "createdAt": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/events")
async def list_events():
    """View queued events"""
    return {
        "queued": len(event_queue),
        "events": event_queue,
    }

@app.post("/events/flush")
async def flush_events():
    """Manually flush events"""
    if not event_queue:
        return {"flushed": 0, "status": "empty"}

    try:
        events = [Event(**e) for e in event_queue.copy()]
        response = sdk.send_events_batch(events)
        count = len(event_queue)
        event_queue.clear()
        return {"flushed": count, "response": response}
    except ShreError as e:
        return JSONResponse({"error": str(e)}, status_code=500)

def queue_event(event_dict):
    """Add event to queue"""
    event_queue.append(event_dict)
    print(f"Queued event: {event_dict['eventName']} (total: {len(event_queue)})")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
