"""Type definitions for the AROS POS SDK.

All types are plain dataclasses — no external dependencies required.
Compatible with Python 3.8+.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Supported vendors
# ---------------------------------------------------------------------------

SUPPORTED_VENDORS = frozenset(
    [
        "mobilepos",
        "verifone-commander",
        "verifone-ruby",
        "ncr-aloha",
        "ncr-counterpoint",
        "ncr-voyix",
        "gilbarco-passport",
        "gilbarco-flexpay",
        "wayne-fusion",
        "oracle-simphony",
        "clover",
        "square",
        "toast",
        "lightspeed",
        "shopify-pos",
        "generic",
    ]
)


def is_valid_vendor(vendor: str) -> bool:
    """Return True if *vendor* is a known vendor or matches the custom-* pattern."""
    return vendor in SUPPORTED_VENDORS or vendor.startswith("custom-")


# ---------------------------------------------------------------------------
# SDK configuration
# ---------------------------------------------------------------------------


@dataclass
class ArosPosConfig:
    """Configuration passed to :func:`create_aros_pos`."""

    endpoint: str
    tenant_id: str
    vendor: str
    device_id: str
    api_key: str
    timeout_s: int = 10
    offline_queue: bool = True
    max_queue_size: int = 500
    flush_interval_s: float = 5.0


# ---------------------------------------------------------------------------
# Connexus event
# ---------------------------------------------------------------------------


@dataclass
class ConnexusEvent:
    """A single POS event destined for the Connexus ingest endpoint."""

    vendor: str
    event_type: str
    data: Dict[str, Any]
    device_id: str
    tenant_id: str
    timestamp: str  # ISO-8601


# ---------------------------------------------------------------------------
# Intelligence response types
# ---------------------------------------------------------------------------


@dataclass
class Recommendation:
    """A single product recommendation."""

    item_id: str = ""
    name: str = ""
    confidence: float = 0.0
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationResponse:
    """Response from POST /v1/pos/recommend."""

    recommendations: List[Recommendation] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuickOrderItem:
    """A single quick-order item."""

    item_id: str = ""
    name: str = ""
    frequency: int = 0
    last_purchased: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuickOrderResponse:
    """Response from POST /v1/pos/quick-order."""

    items: List[QuickOrderItem] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CashierMessage:
    """A single cashier message."""

    message_id: str = ""
    content: str = ""
    priority: str = "normal"
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessagesResponse:
    """Response from GET /v1/pos/messages/{deviceId}."""

    messages: List[CashierMessage] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsResponse:
    """Response from GET /v1/pos/analytics."""

    data: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)
