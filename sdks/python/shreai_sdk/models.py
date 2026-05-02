"""Data models for Shre SDK"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Any, Dict


@dataclass
class Event:
    """Analytics event to send to Shre"""

    event_id: str
    event_name: str
    entity_type: str
    entity_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        result = {
            "eventId": self.event_id,
            "eventName": self.event_name,
            "entityType": self.entity_type,
        }

        if self.entity_id:
            result["entityId"] = self.entity_id

        if self.timestamp:
            result["timestamp"] = self.timestamp.isoformat()

        if self.metadata:
            result["metadata"] = self.metadata

        return result


@dataclass
class EventsResponse:
    """Response from /v1/events/batch endpoint"""

    accepted: int
    rejected: int
    trackingEnabled: bool
    nextFlushSeconds: int


@dataclass
class SessionResponse:
    """Response from /v1/sdk/session endpoint"""

    accessToken: str
    expiresIn: int
    tokenType: str

    @property
    def access_token(self) -> str:
        """Alias for camelCase field"""
        return self.accessToken

    @property
    def expires_in(self) -> int:
        """Alias for camelCase field"""
        return self.expiresIn

    @property
    def token_type(self) -> str:
        """Alias for camelCase field"""
        return self.tokenType


@dataclass
class ConfigResponse:
    """Response from /v1/sdk/config endpoint"""

    trackingEnabled: bool
    disabledEvents: list[str]
    piiMasking: bool
    maxQueueSize: int
    flushIntervalSeconds: int
    batchSize: int
    sinkConfigured: bool

    @property
    def tracking_enabled(self) -> bool:
        """Alias for camelCase field"""
        return self.trackingEnabled

    @property
    def disabled_events(self) -> list[str]:
        """Alias for camelCase field"""
        return self.disabledEvents

    @property
    def pii_masking(self) -> bool:
        """Alias for camelCase field"""
        return self.piiMasking

    @property
    def max_queue_size(self) -> int:
        """Alias for camelCase field"""
        return self.maxQueueSize

    @property
    def flush_interval_seconds(self) -> int:
        """Alias for camelCase field"""
        return self.flushIntervalSeconds

    @property
    def batch_size(self) -> int:
        """Alias for camelCase field"""
        return self.batchSize

    @property
    def sink_configured(self) -> bool:
        """Alias for camelCase field"""
        return self.sinkConfigured


@dataclass
class HeartbeatResponse:
    """Response from /v1/sdk/heartbeat endpoint"""

    ok: bool
    serverTime: str

    @property
    def server_time(self) -> str:
        """Alias for camelCase field"""
        return self.serverTime
