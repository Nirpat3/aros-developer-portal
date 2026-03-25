"""AROS POS SDK — zero-dependency Python client for the Connexus API.

Usage::

    from aros_pos import create_aros_pos

    pos = create_aros_pos(
        endpoint="https://aros.example.com",
        tenant_id="store-42",
        vendor="verifone-commander",
        device_id="REG-001",
        api_key="ak_live_...",
    )

    pos.item_scanned("012345", 9.99)
    recs = pos.get_recommendations("012345")

Compatible with Python 3.8+ using only the standard library.
"""

from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

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
    is_valid_vendor,
)

logger = logging.getLogger("aros_pos")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _strip_trailing_slash(url: str) -> str:
    return url.rstrip("/")


# ---------------------------------------------------------------------------
# ArosPosClient
# ---------------------------------------------------------------------------


class ArosPosClient:
    """Stateful POS client with offline queue and auto-flush.

    Do **not** instantiate directly — use :func:`create_aros_pos`.
    """

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, config: ArosPosConfig) -> None:
        if not is_valid_vendor(config.vendor):
            raise ValueError(
                f"Unknown vendor '{config.vendor}'. "
                "Use a supported vendor or the 'custom-*' prefix."
            )

        self._cfg = config
        self._endpoint = _strip_trailing_slash(config.endpoint)
        self._headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
            "X-Tenant-Id": config.tenant_id,
            "X-Device-Id": config.device_id,
        }

        # Offline queue
        self._queue: List[Dict[str, Any]] = []
        self._queue_lock = threading.Lock()
        self._flush_timer: Optional[threading.Timer] = None
        self._closed = False

        if config.offline_queue:
            self._schedule_flush()

    # ------------------------------------------------------------------
    # HTTP transport (stdlib only)
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute an HTTP request and return the parsed JSON response."""
        url = f"{self._endpoint}{path}"
        if query:
            qs = "&".join(
                f"{urllib.request.quote(k)}={urllib.request.quote(str(v))}"
                for k, v in query.items()
            )
            url = f"{url}?{qs}"

        data_bytes: Optional[bytes] = None
        if body is not None:
            data_bytes = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers=self._headers,
            method=method,
        )

        try:
            with urllib.request.urlopen(
                req, timeout=self._cfg.timeout_s
            ) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8")
            except Exception:
                pass
            logger.error(
                "HTTP %s %s -> %s: %s", method, path, exc.code, err_body
            )
            raise
        except urllib.error.URLError as exc:
            # Network unreachable — caller decides whether to queue
            logger.warning("Network error for %s %s: %s", method, path, exc.reason)
            raise

    # ------------------------------------------------------------------
    # Device registration
    # ------------------------------------------------------------------

    def register(self, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Register this device with the Connexus platform.

        Returns the raw JSON response from ``POST /v1/connexus/register``.
        """
        payload: Dict[str, Any] = {
            "vendor": self._cfg.vendor,
            "deviceId": self._cfg.device_id,
            "tenantId": self._cfg.tenant_id,
        }
        if meta:
            payload["meta"] = meta
        return self._request("POST", "/v1/connexus/register", body=payload)

    # ------------------------------------------------------------------
    # Event helpers (fire-and-forget)
    # ------------------------------------------------------------------

    def _build_event(
        self, event_type: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "vendor": self._cfg.vendor,
            "eventType": event_type,
            "data": data,
            "deviceId": self._cfg.device_id,
            "tenantId": self._cfg.tenant_id,
            "timestamp": _now_iso(),
        }

    def _fire(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send an event — falls back to offline queue on network failure."""
        evt = self._build_event(event_type, data)
        try:
            self._request("POST", "/v1/connexus/ingest", body=evt)
        except Exception:
            if self._cfg.offline_queue:
                self._enqueue(evt)
            else:
                raise

    # ------------------------------------------------------------------
    # Offline queue
    # ------------------------------------------------------------------

    def _enqueue(self, event: Dict[str, Any]) -> None:
        with self._queue_lock:
            if len(self._queue) >= self._cfg.max_queue_size:
                logger.warning(
                    "Offline queue full (%d). Dropping oldest event.",
                    self._cfg.max_queue_size,
                )
                self._queue.pop(0)
            self._queue.append(event)
            logger.debug("Queued event (queue size: %d)", len(self._queue))

    def _schedule_flush(self) -> None:
        if self._closed:
            return
        self._flush_timer = threading.Timer(
            self._cfg.flush_interval_s, self._auto_flush
        )
        self._flush_timer.daemon = True
        self._flush_timer.start()

    def _auto_flush(self) -> None:
        """Attempt to flush the offline queue, then reschedule."""
        self.flush()
        self._schedule_flush()

    def flush(self) -> int:
        """Flush all queued events to the ingest endpoint.

        Returns the number of events successfully sent.
        """
        with self._queue_lock:
            if not self._queue:
                return 0
            batch = list(self._queue)
            self._queue.clear()

        try:
            self._request(
                "POST", "/v1/connexus/ingest", body={"events": batch}
            )
            logger.info("Flushed %d queued events", len(batch))
            return len(batch)
        except Exception:
            # Put them back for the next attempt
            with self._queue_lock:
                self._queue = batch + self._queue
                # Trim to max
                over = len(self._queue) - self._cfg.max_queue_size
                if over > 0:
                    self._queue = self._queue[over:]
            logger.warning(
                "Flush failed — %d events re-queued", len(batch)
            )
            return 0

    @property
    def queue_size(self) -> int:
        """Current number of events in the offline queue."""
        with self._queue_lock:
            return len(self._queue)

    # ------------------------------------------------------------------
    # Fire-and-forget event methods
    # ------------------------------------------------------------------

    def item_scanned(
        self,
        barcode: str,
        price: float,
        *,
        quantity: int = 1,
        description: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an item scan."""
        data: Dict[str, Any] = {
            "barcode": barcode,
            "price": price,
            "quantity": quantity,
        }
        if description:
            data["description"] = description
        if extra:
            data.update(extra)
        self._fire("ItemSale", data)

    def transaction_complete(
        self,
        transaction_id: str,
        total: float,
        *,
        items_count: int = 0,
        payment_method: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a completed transaction."""
        data: Dict[str, Any] = {
            "transactionId": transaction_id,
            "total": total,
        }
        if items_count:
            data["itemsCount"] = items_count
        if payment_method:
            data["paymentMethod"] = payment_method
        if extra:
            data.update(extra)
        self._fire("TransactionComplete", data)

    def void_line(
        self,
        barcode: str,
        price: float,
        *,
        reason: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Void a single line item."""
        data: Dict[str, Any] = {"barcode": barcode, "price": price}
        if reason:
            data["reason"] = reason
        if extra:
            data.update(extra)
        self._fire("VoidLine", data)

    def void_transaction(
        self,
        transaction_id: str,
        *,
        reason: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Void an entire transaction."""
        data: Dict[str, Any] = {"transactionId": transaction_id}
        if reason:
            data["reason"] = reason
        if extra:
            data.update(extra)
        self._fire("VoidTransaction", data)

    def return_item(
        self,
        barcode: str,
        price: float,
        *,
        transaction_id: str = "",
        reason: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a returned item."""
        data: Dict[str, Any] = {"barcode": barcode, "price": price}
        if transaction_id:
            data["transactionId"] = transaction_id
        if reason:
            data["reason"] = reason
        if extra:
            data.update(extra)
        self._fire("Return", data)

    def discount_applied(
        self,
        barcode: str,
        original_price: float,
        discount_amount: float,
        *,
        discount_type: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a discount applied to an item."""
        data: Dict[str, Any] = {
            "barcode": barcode,
            "originalPrice": original_price,
            "discountAmount": discount_amount,
        }
        if discount_type:
            data["discountType"] = discount_type
        if extra:
            data.update(extra)
        self._fire("DiscountApplied", data)

    def price_override(
        self,
        barcode: str,
        original_price: float,
        new_price: float,
        *,
        reason: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a manual price override."""
        data: Dict[str, Any] = {
            "barcode": barcode,
            "originalPrice": original_price,
            "newPrice": new_price,
        }
        if reason:
            data["reason"] = reason
        if extra:
            data.update(extra)
        self._fire("PriceOverride", data)

    def no_sale(
        self,
        *,
        reason: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a no-sale (drawer open without transaction)."""
        data: Dict[str, Any] = {}
        if reason:
            data["reason"] = reason
        if extra:
            data.update(extra)
        self._fire("NoSale", data)

    def customer_identified(
        self,
        customer_id: str,
        *,
        loyalty_tier: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record customer identification (loyalty scan, etc.)."""
        data: Dict[str, Any] = {"customerId": customer_id}
        if loyalty_tier:
            data["loyaltyTier"] = loyalty_tier
        if extra:
            data.update(extra)
        self._fire("CustomerIdentified", data)

    def fuel_dispensed(
        self,
        pump: Union[int, str],
        gallons: float,
        price_per_gallon: float,
        total: float,
        *,
        fuel_grade: str = "",
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a fuel dispensing event (c-store / fuel specific)."""
        data: Dict[str, Any] = {
            "pump": pump,
            "gallons": gallons,
            "pricePerGallon": price_per_gallon,
            "total": total,
        }
        if fuel_grade:
            data["fuelGrade"] = fuel_grade
        if extra:
            data.update(extra)
        self._fire("FuelDispensed", data)

    def send_event(
        self, event_type: str, data: Dict[str, Any]
    ) -> None:
        """Send an arbitrary custom event."""
        self._fire(event_type, data)

    def learn_basket(self, items: List[Dict[str, Any]]) -> None:
        """Teach basket-level associations for recommendation training.

        *items* is a list of dicts, each with at least ``barcode`` and ``price``.
        Sent to ``POST /v1/connexus/ingest/learn``.
        """
        payload = {
            "vendor": self._cfg.vendor,
            "deviceId": self._cfg.device_id,
            "tenantId": self._cfg.tenant_id,
            "items": items,
            "timestamp": _now_iso(),
        }
        try:
            self._request("POST", "/v1/connexus/ingest/learn", body=payload)
        except Exception:
            if self._cfg.offline_queue:
                self._enqueue({**payload, "eventType": "_LearnBasket"})
            else:
                raise

    # ------------------------------------------------------------------
    # Intelligence methods (synchronous, return data)
    # ------------------------------------------------------------------

    def get_recommendations(
        self,
        item_id: str,
        *,
        limit: int = 5,
    ) -> RecommendationResponse:
        """Fetch product recommendations for an item.

        Calls ``POST /v1/pos/recommend``.
        """
        body = {
            "itemId": item_id,
            "tenantId": self._cfg.tenant_id,
            "limit": limit,
        }
        raw = self._request("POST", "/v1/pos/recommend", body=body)
        recs = [
            Recommendation(
                item_id=r.get("itemId", r.get("item_id", "")),
                name=r.get("name", ""),
                confidence=r.get("confidence", 0.0),
                reason=r.get("reason", ""),
                metadata=r.get("metadata", {}),
            )
            for r in raw.get("recommendations", [])
        ]
        return RecommendationResponse(recommendations=recs, raw=raw)

    def get_quick_order(
        self,
        customer_id: str,
        *,
        limit: int = 10,
    ) -> QuickOrderResponse:
        """Fetch a customer's frequent items for quick re-order.

        Calls ``POST /v1/pos/quick-order``.
        """
        body = {
            "customerId": customer_id,
            "tenantId": self._cfg.tenant_id,
            "limit": limit,
        }
        raw = self._request("POST", "/v1/pos/quick-order", body=body)
        items = [
            QuickOrderItem(
                item_id=i.get("itemId", i.get("item_id", "")),
                name=i.get("name", ""),
                frequency=i.get("frequency", 0),
                last_purchased=i.get("lastPurchased", i.get("last_purchased", "")),
                metadata=i.get("metadata", {}),
            )
            for i in raw.get("items", [])
        ]
        return QuickOrderResponse(items=items, raw=raw)

    def get_messages(self) -> MessagesResponse:
        """Fetch cashier messages for this device.

        Calls ``GET /v1/pos/messages/{deviceId}``.
        """
        raw = self._request(
            "GET",
            f"/v1/pos/messages/{self._cfg.device_id}",
            query={"tenantId": self._cfg.tenant_id},
        )
        msgs = [
            CashierMessage(
                message_id=m.get("messageId", m.get("message_id", "")),
                content=m.get("content", ""),
                priority=m.get("priority", "normal"),
                created_at=m.get("createdAt", m.get("created_at", "")),
                metadata=m.get("metadata", {}),
            )
            for m in raw.get("messages", [])
        ]
        return MessagesResponse(messages=msgs, raw=raw)

    def ack_message(self, message_id: str) -> Dict[str, Any]:
        """Acknowledge a cashier message.

        Calls ``POST /v1/pos/messages/{messageId}/ack``.
        """
        return self._request(
            "POST",
            f"/v1/pos/messages/{message_id}/ack",
            body={"deviceId": self._cfg.device_id, "tenantId": self._cfg.tenant_id},
        )

    def get_analytics(self, *, minutes: int = 60) -> AnalyticsResponse:
        """Fetch real-time analytics for the tenant.

        Calls ``GET /v1/pos/analytics``.
        """
        raw = self._request(
            "GET",
            "/v1/pos/analytics",
            query={
                "tenantId": self._cfg.tenant_id,
                "minutes": str(minutes),
            },
        )
        return AnalyticsResponse(data=raw.get("data", raw), raw=raw)

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Flush remaining events and stop the background timer."""
        self._closed = True
        if self._flush_timer is not None:
            self._flush_timer.cancel()
            self._flush_timer = None
        self.flush()

    def __enter__(self) -> "ArosPosClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_aros_pos(
    *,
    endpoint: str,
    tenant_id: str,
    vendor: str,
    device_id: str,
    api_key: str,
    timeout_s: int = 10,
    offline_queue: bool = True,
    max_queue_size: int = 500,
    flush_interval_s: float = 5.0,
) -> ArosPosClient:
    """Create and return an :class:`ArosPosClient`.

    This is the primary entry point for the SDK::

        from aros_pos import create_aros_pos

        pos = create_aros_pos(
            endpoint="https://aros.example.com",
            tenant_id="store-42",
            vendor="verifone-commander",
            device_id="REG-001",
            api_key="ak_live_...",
        )
    """
    config = ArosPosConfig(
        endpoint=endpoint,
        tenant_id=tenant_id,
        vendor=vendor,
        device_id=device_id,
        api_key=api_key,
        timeout_s=timeout_s,
        offline_queue=offline_queue,
        max_queue_size=max_queue_size,
        flush_interval_s=flush_interval_s,
    )
    return ArosPosClient(config)
