"""ShreAI Python SDK v2 — single file, stdlib only.

Spec: aros-developer-portal/sdks/SHARED-SDK-SPEC.md

Quick start:

    from shreai import ShreAI

    sa = ShreAI(
        endpoint="https://apiauth.shre.ai",
        events_endpoint="https://events.shre.ai",
        tenant_id="merchant_123",
        app="rapid_pos",
        mode="read_only",
    )
    sa.start()
    sa.track("price_updated", entity_type="item", entity_id="UPC_012345678905",
             metadata={"old": 10.49, "new": 10.99})
    # ... later, on shutdown:
    sa.stop()
"""
from __future__ import annotations
import json
import os
import re
import threading
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from typing import Any, Callable, Optional

SDK_VERSION = "python/2.0.0"
APP_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
BACKOFF_S = (5, 15, 30, 60, 300)


class ShreAIError(Exception):
    pass


class ShreAI:
    def __init__(
        self,
        endpoint: str,
        tenant_id: str,
        app: str,
        events_endpoint: Optional[str] = None,
        store_id: Optional[str] = None,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        mode: str = "read_only",
        bootstrap_key: Optional[str] = None,
        sdk_version: str = SDK_VERSION,
        flush_interval_seconds: int = 10,
        batch_size: int = 50,
        max_queue_size: int = 5000,
        timeout_s: float = 8.0,
        on_error: Optional[Callable[[BaseException, str], None]] = None,
        on_flush: Optional[Callable[[int, int], None]] = None,
    ):
        if not _valid_url(endpoint):
            raise ShreAIError(f"invalid endpoint URL: {endpoint!r}")
        if _hostname(endpoint).startswith("downloads."):
            raise ShreAIError(
                f"endpoint host '{_hostname(endpoint)}' looks like a download host. "
                "Use https://apiauth.shre.ai (control) and https://events.shre.ai (data)."
            )
        ev = events_endpoint or endpoint
        if not _valid_url(ev):
            raise ShreAIError(f"invalid eventsEndpoint URL: {ev!r}")
        if _hostname(ev).startswith("downloads."):
            raise ShreAIError(f"eventsEndpoint host '{_hostname(ev)}' looks like a download host.")
        if not APP_PATTERN.match(app):
            raise ShreAIError(f"app must match {APP_PATTERN.pattern}: {app!r}")
        if mode == "read_write" and not bootstrap_key:
            raise ShreAIError("read_write mode requires bootstrap_key")

        self._endpoint = endpoint.rstrip("/")
        self._events_endpoint = ev.rstrip("/")
        self._tenant_id = tenant_id
        self._store_id = store_id
        self._user_id = user_id
        self._role = role
        self._app = app
        self._mode = mode
        self._bootstrap_key = bootstrap_key
        self._sdk_version = sdk_version
        self._flush_interval = flush_interval_seconds
        self._batch_size = batch_size
        self._max_queue = max_queue_size
        self._timeout_s = timeout_s
        self.on_error = on_error
        self.on_flush = on_flush

        self._queue: deque = deque(maxlen=max_queue_size)
        self._lock = threading.Lock()
        self._sdk_token: Optional[str] = None
        self._session_id: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._tracking_enabled: bool = True
        self._disabled_events: set[str] = set()
        self._retry_attempt = 0
        self._stopped = False
        self._flush_thread: Optional[threading.Thread] = None
        self._config_thread: Optional[threading.Thread] = None

    # ─── public API ─────────────────────────────────────────────────────
    def start(self) -> None:
        self._bootstrap()
        self._refresh_remote_config()
        self._start_flush_thread()
        self._start_config_thread()

    def track(
        self,
        name: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        if self._stopped or not self._tracking_enabled or name in self._disabled_events:
            return
        evt = {
            "eventId": str(uuid.uuid4()),
            "eventName": name,
            "metadata": metadata or {},
            "timestamp": _iso(timestamp or time.time()),
        }
        if entity_type:
            evt["entityType"] = entity_type
        if entity_id:
            evt["entityId"] = entity_id
        with self._lock:
            self._queue.append(evt)

    def flush(self) -> dict:
        with self._lock:
            if not self._queue:
                return {"accepted": 0, "rejected": 0, "trackingEnabled": self._tracking_enabled, "nextFlushSeconds": self._flush_interval}
            batch = []
            for _ in range(min(self._batch_size, len(self._queue))):
                batch.append(self._queue.popleft())
        try:
            ack = self._post_batch(batch)
            self._retry_attempt = 0
            if self.on_flush:
                self.on_flush(ack.get("accepted", 0), ack.get("rejected", 0))
            ns = ack.get("nextFlushSeconds")
            if isinstance(ns, int) and ns > 0 and ns != self._flush_interval:
                self._flush_interval = ns
            return ack
        except _StatusError as e:
            with self._lock:
                # requeue at front
                for evt in reversed(batch):
                    self._queue.appendleft(evt)
            if self.on_flush:
                self.on_flush(0, len(batch))
            if e.status == 401:
                try:
                    self._bootstrap()
                except Exception as err:
                    if self.on_error:
                        self.on_error(err, "bootstrap")
            elif e.status == 403:
                self._tracking_enabled = False
            elif e.status == 429 or e.status >= 500:
                self._schedule_backoff()
            else:
                if self.on_error:
                    self.on_error(e, "flush")
            return {"accepted": 0, "rejected": len(batch), "error": str(e)}
        except Exception as err:
            with self._lock:
                for evt in reversed(batch):
                    self._queue.appendleft(evt)
            if self.on_error:
                self.on_error(err, "flush")
            self._schedule_backoff()
            return {"accepted": 0, "rejected": len(batch), "error": str(err)}

    def heartbeat(self, device_id: Optional[str] = None) -> None:
        body = {
            "tenantId": self._tenant_id,
            "app": self._app,
            "sdkVersion": self._sdk_version,
            "eventsQueued": len(self._queue),
        }
        if self._store_id:
            body["storeId"] = self._store_id
        if device_id:
            body["deviceId"] = device_id
        try:
            self._http_post(f"{self._events_endpoint}/v1/sdk/heartbeat", body)
        except Exception:
            pass

    def stop(self) -> None:
        self._stopped = True
        try:
            self.flush()  # final drain
        except Exception:
            pass

    # ─── internals ──────────────────────────────────────────────────────
    def _bootstrap(self) -> None:
        body = {
            "tenantId": self._tenant_id,
            "app": self._app,
            "mode": self._mode,
            "sdkVersion": self._sdk_version,
        }
        if self._store_id:
            body["storeId"] = self._store_id
        if self._user_id:
            body["userId"] = self._user_id
        if self._role:
            body["role"] = self._role
        if self._bootstrap_key:
            body["bootstrapKey"] = self._bootstrap_key
        data = self._http_post(f"{self._endpoint}/v1/sdk/session", body)
        self._sdk_token = data.get("sdkToken")
        self._session_id = data.get("sessionId")
        self._tracking_enabled = bool(data.get("trackingEnabled", True))
        exp = data.get("expiresIn")
        if isinstance(exp, int):
            self._token_expires_at = time.time() + exp

    def _refresh_remote_config(self) -> None:
        try:
            data = self._http_get(f"{self._endpoint}/v1/sdk/config")
        except Exception:
            return
        if "trackingEnabled" in data:
            self._tracking_enabled = bool(data["trackingEnabled"])
        if "disabledEvents" in data and isinstance(data["disabledEvents"], list):
            self._disabled_events = set(data["disabledEvents"])

    def _post_batch(self, events: list[dict]) -> dict:
        if self._mode == "read_write" and self._token_expires_at - time.time() < 60:
            self._bootstrap()
        return self._http_post(f"{self._events_endpoint}/v1/events/batch", {"events": events})

    def _http_post(self, url: str, body: dict) -> dict:
        return self._http(url, method="POST", body=body)

    def _http_get(self, url: str) -> dict:
        return self._http(url, method="GET")

    def _http(self, url: str, method: str, body: Optional[dict] = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        # Cloudflare's WAF rejects default Python UA (error 1010). Use the SDK identity instead.
        req.add_header("User-Agent", f"shreai-sdk/{self._sdk_version}")
        req.add_header("Accept", "application/json")
        req.add_header("X-Shre-Tenant", self._tenant_id)
        req.add_header("X-Shre-App", self._app)
        req.add_header("X-Shre-SDK-Version", self._sdk_version)
        if self._store_id:
            req.add_header("X-Shre-Store", self._store_id)
        if self._sdk_token:
            req.add_header("Authorization", f"Bearer {self._sdk_token}")
        try:
            with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                return json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            err = _StatusError(e.code, e.read().decode(errors="replace")[:300])
            raise err

    def _schedule_backoff(self) -> None:
        idx = min(self._retry_attempt, len(BACKOFF_S) - 1)
        delay = BACKOFF_S[idx]
        self._retry_attempt += 1
        timer = threading.Timer(delay, self.flush)
        timer.daemon = True
        timer.start()

    def _start_flush_thread(self) -> None:
        def loop():
            while not self._stopped:
                time.sleep(max(2, self._flush_interval))
                try:
                    self.flush()
                except Exception:
                    pass

        t = threading.Thread(target=loop, daemon=True, name="shreai-flush")
        t.start()
        self._flush_thread = t

    def _start_config_thread(self) -> None:
        def loop():
            while not self._stopped:
                time.sleep(300)
                try:
                    self._refresh_remote_config()
                except Exception:
                    pass

        t = threading.Thread(target=loop, daemon=True, name="shreai-config")
        t.start()
        self._config_thread = t


class _StatusError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"HTTP {status}: {message}")
        self.status = status
        self.message = message


def _iso(epoch_seconds: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch_seconds))


def _valid_url(s: str) -> bool:
    p = urllib.parse.urlparse(s)
    return p.scheme in ("http", "https") and bool(p.netloc)


def _hostname(url: str) -> str:
    return (urllib.parse.urlparse(url).hostname or "").lower()


# Final-drain on interpreter exit
import atexit  # noqa: E402

_active_instances: list[ShreAI] = []


def _drain_all():
    for sa in list(_active_instances):
        try:
            sa.stop()
        except Exception:
            pass


atexit.register(_drain_all)

# Auto-register every instance for atexit drain
_orig_init = ShreAI.__init__


def _tracked_init(self, *args, **kwargs):
    _orig_init(self, *args, **kwargs)
    _active_instances.append(self)


ShreAI.__init__ = _tracked_init  # type: ignore
