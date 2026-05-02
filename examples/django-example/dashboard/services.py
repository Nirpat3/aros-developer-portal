import sys
import os
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, '/Users/aibot/Documents/Projects/shreai/aros-developer-portal/sdks/python')

from shreai_sdk import ShreSDK, Event
from shreai_sdk.exceptions import ShreError

sdk = ShreSDK(tenant_id="dev-tenant-001")
event_log = []

def track_event(event_name, entity_type, entity_id, metadata=None):
    """Track an event via Shre SDK"""
    try:
        event = Event(
            eventId=str(uuid4()),
            eventName=event_name,
            entityType=entity_type,
            entityId=entity_id,
            metadata=metadata or {},
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

        response = sdk.send_events_batch([event])

        # Log to local event log for demo
        event_log.append({
            "event": event_name,
            "entity": entity_id,
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat(),
        })

        return response
    except ShreError as e:
        event_log.append({
            "event": event_name,
            "entity": entity_id,
            "status": f"error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
        })
        print(f"Event tracking error: {e}")
        return None

def get_event_log():
    """Get recent events"""
    return event_log[-50:]  # Last 50 events
