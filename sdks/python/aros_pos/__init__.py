"""AROS POS SDK — zero-dependency Python client for the Connexus API.

Quick start::

    from aros_pos import create_aros_pos

    pos = create_aros_pos(
        endpoint="https://aros.example.com",
        tenant_id="store-42",
        vendor="verifone-commander",
        device_id="REG-001",
        api_key="ak_live_...",
    )

    # Fire-and-forget events
    pos.item_scanned("012345", 9.99)
    pos.transaction_complete("TXN-001", 42.50)

    # Intelligence queries
    recs = pos.get_recommendations("012345")
    for r in recs.recommendations:
        print(r.name, r.confidence)

    pos.close()
"""

from .client import ArosPosClient, create_aros_pos
from .types import (
    AnalyticsResponse,
    ArosPosConfig,
    CashierMessage,
    ConnexusEvent,
    MessagesResponse,
    QuickOrderItem,
    QuickOrderResponse,
    Recommendation,
    RecommendationResponse,
    SUPPORTED_VENDORS,
)

__version__ = "1.0.0"

__all__ = [
    "create_aros_pos",
    "ArosPosClient",
    "ArosPosConfig",
    "ConnexusEvent",
    "Recommendation",
    "RecommendationResponse",
    "QuickOrderItem",
    "QuickOrderResponse",
    "CashierMessage",
    "MessagesResponse",
    "AnalyticsResponse",
    "SUPPORTED_VENDORS",
    "__version__",
]
