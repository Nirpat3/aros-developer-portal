"""Shre AI SDK Client"""

import json
import requests
from typing import Optional, Callable
from datetime import datetime, timezone, timedelta
from .models import (
    Event,
    EventsResponse,
    SessionResponse,
    ConfigResponse,
    HeartbeatResponse,
)
from .exceptions import ShreError


class ShreSDK:
    """Shre AI Event SDK for Python

    Contract: v2.0.0 (Locked May 2, 2026)
    """

    def __init__(
        self,
        tenant_id: str,
        app_platform: str = "python",
        base_url: str = "https://apiauth.shre.ai",
    ):
        """Initialize Shre SDK

        Args:
            tenant_id: Tenant identifier (workspace ID)
            app_platform: App platform (ios, android, web, python, dotnet)
            base_url: API base URL
        """
        self.tenant_id = tenant_id
        self.app_platform = app_platform
        self.base_url = base_url.rstrip("/")
        self.auth_token: Optional[str] = None
        self.session_expiry: Optional[datetime] = None
        self.session = requests.Session()

    # MARK: - Public API

    def send_events_batch(self, events: list[Event]) -> EventsResponse:
        """Send batch of analytics events (read-only mode)

        No authentication required.

        Args:
            events: List of Event objects

        Returns:
            EventsResponse with accepted/rejected counts

        Raises:
            ShreError: If request fails
        """
        url = f"{self.base_url}/v1/events/batch"
        headers = {
            "Content-Type": "application/json",
            "x-shre-tenant": self.tenant_id,
            "x-shre-app": self.app_platform,
        }
        payload = {"events": [event.to_dict() for event in events]}

        response = self._request("POST", url, json=payload, headers=headers)
        return EventsResponse(**response)

    def create_session(self, bootstrap_key: str) -> SessionResponse:
        """Authenticate and mint JWT token (read-write mode)

        Requires bootstrap key.

        Args:
            bootstrap_key: Public bootstrap key for authentication

        Returns:
            SessionResponse with access token

        Raises:
            ShreError: If request fails
        """
        url = f"{self.base_url}/v1/sdk/session"
        headers = {
            "Content-Type": "application/json",
            "x-shre-tenant": self.tenant_id,
            "x-shre-app": bootstrap_key,
        }

        response = self._request("POST", url, json={}, headers=headers)
        session_resp = SessionResponse(**response)

        # Store token for future authenticated requests
        self.auth_token = session_resp.access_token
        self.session_expiry = datetime.now(timezone.utc).replace(
            microsecond=0
        ) + timedelta(seconds=session_resp.expires_in)

        return session_resp

    def get_config(self) -> ConfigResponse:
        """Fetch SDK configuration for tenant

        Returns:
            ConfigResponse with per-tenant settings

        Raises:
            ShreError: If request fails
        """
        url = f"{self.base_url}/v1/sdk/config"
        headers = {
            "x-shre-tenant": self.tenant_id,
        }

        response = self._request("GET", url, headers=headers)
        return ConfigResponse(**response)

    def send_heartbeat(
        self,
        device_id: str,
        events_queued: int,
        events_sent: int = 0,
    ) -> HeartbeatResponse:
        """Send heartbeat (device liveness signal)

        Args:
            device_id: Unique device identifier
            events_queued: Number of events in queue
            events_sent: Number of events successfully sent

        Returns:
            HeartbeatResponse with server time

        Raises:
            ShreError: If request fails
        """
        url = f"{self.base_url}/v1/sdk/heartbeat"
        headers = {
            "Content-Type": "application/json",
            "x-shre-tenant": self.tenant_id,
            "x-shre-app": self.app_platform,
        }
        payload = {
            "tenantId": self.tenant_id,
            "app": self.app_platform,
            "deviceId": device_id,
            "eventsQueued": events_queued,
            "eventsSent": events_sent,
        }

        response = self._request("POST", url, json=payload, headers=headers)
        return HeartbeatResponse(**response)

    # MARK: - Private Helpers

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """Execute HTTP request with error handling

        Args:
            method: HTTP method (GET, POST, etc)
            url: Full URL
            **kwargs: Additional arguments for requests

        Returns:
            Parsed JSON response

        Raises:
            ShreError: If request fails
        """
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)

            if response.status_code == 400:
                raise ShreError.BadRequest("Bad request (missing headers or invalid JSON)")
            elif response.status_code == 401:
                raise ShreError.Unauthorized("Unauthorized (invalid JWT or bootstrap key)")
            elif response.status_code >= 500:
                raise ShreError.ServerError(f"Server error: {response.status_code}")
            elif not (200 <= response.status_code < 300):
                raise ShreError.NetworkError(
                    f"HTTP {response.status_code}: {response.text}"
                )

            return response.json()

        except requests.RequestException as e:
            raise ShreError.NetworkError(str(e))
        except json.JSONDecodeError as e:
            raise ShreError.NetworkError(f"Invalid JSON response: {str(e)}")
