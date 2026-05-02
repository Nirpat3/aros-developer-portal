"""
Contract tests for Shre SDK v2.0.0

Validates all 4 locked endpoints:
1. POST /v1/events/batch
2. POST /v1/sdk/session
3. GET /v1/sdk/config
4. POST /v1/sdk/heartbeat

Test contract adherence across success, error, and edge cases.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from shreai_sdk import ShreSDK
from shreai_sdk.models import Event, EventsResponse, SessionResponse, ConfigResponse, HeartbeatResponse
from shreai_sdk.exceptions import (
    ShreError,
    BadRequest,
    Unauthorized,
    ServerError,
    NetworkError,
)


# ============================================================================
# MARK: - Fixtures
# ============================================================================


@pytest.fixture
def sdk():
    """Create SDK instance for testing"""
    return ShreSDK(
        tenant_id="test-workspace-123",
        app_platform="python",
        base_url="https://apiauth.shre.ai"
    )


@pytest.fixture
def mock_session():
    """Mock requests.Session"""
    with patch('shreai_sdk.client.requests.Session') as mock:
        yield mock


# ============================================================================
# MARK: - POST /v1/events/batch Tests
# ============================================================================


class TestEventsBatchEndpoint:
    """Contract tests for POST /v1/events/batch"""

    def test_send_events_batch_success_single_event(self, sdk):
        """Should send single event and return EventsResponse"""
        event = Event(
            event_id="evt_001",
            event_name="page_view",
            entity_type="page"
        )

        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "accepted": 1,
                "rejected": 0,
                "trackingEnabled": True,
                "nextFlushSeconds": 30
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.send_events_batch([event])

            # Verify result
            assert isinstance(result, EventsResponse)
            assert result.accepted == 1
            assert result.rejected == 0
            assert result.trackingEnabled is True
            assert result.nextFlushSeconds == 30

            # Verify request
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "POST"
            assert "/v1/events/batch" in call_args[0][1]

    def test_send_events_batch_success_multiple_events(self, sdk):
        """Should send multiple events in single request"""
        events = [
            Event(event_id="evt_001", event_name="page_view", entity_type="page"),
            Event(event_id="evt_002", event_name="button_click", entity_type="button"),
            Event(event_id="evt_003", event_name="form_submit", entity_type="form"),
        ]

        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "accepted": 3,
                "rejected": 0,
                "trackingEnabled": True,
                "nextFlushSeconds": 30
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.send_events_batch(events)

            assert result.accepted == 3
            assert result.rejected == 0

    def test_send_events_batch_with_optional_fields(self, sdk):
        """Should include optional event fields in request"""
        now = datetime.now(timezone.utc)
        event = Event(
            event_id="evt_001",
            event_name="purchase",
            entity_type="transaction",
            entity_id="txn_123",
            timestamp=now,
            metadata={"amount": 99.99, "currency": "USD"}
        )

        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "accepted": 1,
                "rejected": 0,
                "trackingEnabled": True,
                "nextFlushSeconds": 30
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.send_events_batch([event])

            # Verify payload includes optional fields
            call_args = mock_request.call_args
            payload = call_args[1]['json']
            assert payload['events'][0]['entityId'] == 'txn_123'
            assert payload['events'][0]['metadata']['amount'] == 99.99

    def test_send_events_batch_headers_required(self, sdk):
        """Should include required headers: x-shre-tenant, x-shre-app"""
        event = Event(event_id="evt_001", event_name="test", entity_type="test")

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": 1, "rejected": 0, "trackingEnabled": True, "nextFlushSeconds": 30
            }
            mock_request.return_value = mock_response

            sdk.send_events_batch([event])

            call_args = mock_request.call_args
            headers = call_args[1]['headers']
            assert headers['x-shre-tenant'] == 'test-workspace-123'
            assert headers['x-shre-app'] == 'python'
            assert headers['Content-Type'] == 'application/json'

    def test_send_events_batch_no_auth_required(self, sdk):
        """Should NOT require Authorization header"""
        event = Event(event_id="evt_001", event_name="test", entity_type="test")

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accepted": 1, "rejected": 0, "trackingEnabled": True, "nextFlushSeconds": 30
            }
            mock_request.return_value = mock_response

            sdk.send_events_batch([event])

            call_args = mock_request.call_args
            headers = call_args[1]['headers']
            assert 'Authorization' not in headers

    def test_send_events_batch_partial_rejection(self, sdk):
        """Should handle partial rejection response"""
        events = [
            Event(event_id="evt_001", event_name="valid", entity_type="test"),
            Event(event_id="evt_002", event_name="invalid", entity_type="test"),
        ]

        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "accepted": 1,
                "rejected": 1,
                "trackingEnabled": True,
                "nextFlushSeconds": 30
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.send_events_batch(events)

            assert result.accepted == 1
            assert result.rejected == 1

    def test_send_events_batch_empty_list(self, sdk):
        """Should accept empty event list"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "accepted": 0,
                "rejected": 0,
                "trackingEnabled": True,
                "nextFlushSeconds": 30
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.send_events_batch([])

            assert result.accepted == 0
            assert result.rejected == 0

    def test_send_events_batch_bad_request_400(self, sdk):
        """Should raise BadRequest on 400 response"""
        event = Event(event_id="evt_001", event_name="test", entity_type="test")

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Missing required header"
            mock_request.return_value = mock_response

            with pytest.raises(BadRequest):
                sdk.send_events_batch([event])

    def test_send_events_batch_unauthorized_401(self, sdk):
        """Should raise Unauthorized on 401 response"""
        event = Event(event_id="evt_001", event_name="test", entity_type="test")

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Invalid credentials"
            mock_request.return_value = mock_response

            with pytest.raises(Unauthorized):
                sdk.send_events_batch([event])

    def test_send_events_batch_server_error_500(self, sdk):
        """Should raise ServerError on 5xx response"""
        event = Event(event_id="evt_001", event_name="test", entity_type="test")

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_request.return_value = mock_response

            with pytest.raises(ServerError):
                sdk.send_events_batch([event])

    def test_send_events_batch_network_error(self, sdk):
        """Should raise NetworkError on connection failure"""
        event = Event(event_id="evt_001", event_name="test", entity_type="test")

        with patch.object(sdk.session, 'request') as mock_request:
            import requests
            mock_request.side_effect = requests.ConnectionError("Connection refused")

            with pytest.raises(NetworkError):
                sdk.send_events_batch([event])

    def test_send_events_batch_invalid_json_response(self, sdk):
        """Should raise NetworkError on invalid JSON response"""
        event = Event(event_id="evt_001", event_name="test", entity_type="test")

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
            mock_request.return_value = mock_response

            with pytest.raises(NetworkError):
                sdk.send_events_batch([event])


# ============================================================================
# MARK: - POST /v1/sdk/session Tests
# ============================================================================


class TestSessionEndpoint:
    """Contract tests for POST /v1/sdk/session"""

    def test_create_session_success(self, sdk):
        """Should mint JWT token from bootstrap key"""
        bootstrap_key = "pub_key_abc123"

        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "accessToken": "jwt_token_xyz789",
                "expiresIn": 3600,
                "tokenType": "Bearer"
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.create_session(bootstrap_key)

            assert isinstance(result, SessionResponse)
            assert result.accessToken == "jwt_token_xyz789"
            assert result.expiresIn == 3600
            assert result.tokenType == "Bearer"

    def test_create_session_stores_token(self, sdk):
        """Should store token for future authenticated requests"""
        bootstrap_key = "pub_key_abc123"

        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "accessToken": "jwt_token_xyz789",
                "expiresIn": 3600,
                "tokenType": "Bearer"
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.create_session(bootstrap_key)

            assert sdk.auth_token == "jwt_token_xyz789"
            assert sdk.session_expiry is not None

    def test_create_session_headers_required(self, sdk):
        """Should include required headers: x-shre-tenant (required), x-shre-app (bootstrap key)"""
        bootstrap_key = "pub_key_abc123"

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accessToken": "jwt_token_xyz789",
                "expiresIn": 3600,
                "tokenType": "Bearer"
            }
            mock_request.return_value = mock_response

            sdk.create_session(bootstrap_key)

            call_args = mock_request.call_args
            headers = call_args[1]['headers']
            assert headers['x-shre-tenant'] == 'test-workspace-123'
            assert headers['x-shre-app'] == bootstrap_key

    def test_create_session_no_body_required(self, sdk):
        """Should accept empty JSON body"""
        bootstrap_key = "pub_key_abc123"

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accessToken": "jwt_token_xyz789",
                "expiresIn": 3600,
                "tokenType": "Bearer"
            }
            mock_request.return_value = mock_response

            sdk.create_session(bootstrap_key)

            call_args = mock_request.call_args
            assert call_args[1]['json'] == {}

    def test_create_session_token_expiry_calculation(self, sdk):
        """Should calculate expiry time from expiresIn"""
        bootstrap_key = "pub_key_abc123"
        before_call = datetime.now(timezone.utc)

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "accessToken": "jwt_token_xyz789",
                "expiresIn": 3600,
                "tokenType": "Bearer"
            }
            mock_request.return_value = mock_response

            sdk.create_session(bootstrap_key)
            after_call = datetime.now(timezone.utc)

            # Should expire approximately in 3600 seconds
            expected_expiry = before_call + timedelta(seconds=3600)
            assert sdk.session_expiry >= expected_expiry - timedelta(seconds=1)
            assert sdk.session_expiry <= after_call + timedelta(seconds=3600 + 1)

    def test_create_session_unauthorized_401(self, sdk):
        """Should raise Unauthorized on 401 response"""
        bootstrap_key = "invalid_key"

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Invalid bootstrap key"
            mock_request.return_value = mock_response

            with pytest.raises(Unauthorized):
                sdk.create_session(bootstrap_key)

    def test_create_session_bad_request_400(self, sdk):
        """Should raise BadRequest on 400 response"""
        bootstrap_key = "pub_key_abc123"

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Missing x-shre-tenant header"
            mock_request.return_value = mock_response

            with pytest.raises(BadRequest):
                sdk.create_session(bootstrap_key)

    def test_create_session_server_error_500(self, sdk):
        """Should raise ServerError on 5xx response"""
        bootstrap_key = "pub_key_abc123"

        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"
            mock_request.return_value = mock_response

            with pytest.raises(ServerError):
                sdk.create_session(bootstrap_key)

    def test_create_session_network_error(self, sdk):
        """Should raise NetworkError on connection failure"""
        bootstrap_key = "pub_key_abc123"

        with patch.object(sdk.session, 'request') as mock_request:
            import requests
            mock_request.side_effect = requests.ConnectionError("Connection refused")

            with pytest.raises(NetworkError):
                sdk.create_session(bootstrap_key)

    def test_create_session_properties_alias(self, sdk):
        """Should provide snake_case property aliases"""
        bootstrap_key = "pub_key_abc123"

        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "accessToken": "jwt_token_xyz789",
                "expiresIn": 3600,
                "tokenType": "Bearer"
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.create_session(bootstrap_key)

            # camelCase properties
            assert result.accessToken == "jwt_token_xyz789"
            assert result.expiresIn == 3600
            assert result.tokenType == "Bearer"

            # snake_case aliases
            assert result.access_token == "jwt_token_xyz789"
            assert result.expires_in == 3600
            assert result.token_type == "Bearer"


# ============================================================================
# MARK: - GET /v1/sdk/config Tests
# ============================================================================


class TestConfigEndpoint:
    """Contract tests for GET /v1/sdk/config"""

    def test_get_config_success(self, sdk):
        """Should fetch tenant configuration"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "trackingEnabled": True,
                "disabledEvents": [],
                "piiMasking": False,
                "maxQueueSize": 100,
                "flushIntervalSeconds": 30,
                "batchSize": 10,
                "sinkConfigured": True
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.get_config()

            assert isinstance(result, ConfigResponse)
            assert result.trackingEnabled is True
            assert result.disabledEvents == []
            assert result.piiMasking is False
            assert result.maxQueueSize == 100
            assert result.flushIntervalSeconds == 30
            assert result.batchSize == 10
            assert result.sinkConfigured is True

    def test_get_config_with_disabled_events(self, sdk):
        """Should include disabled events list"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "trackingEnabled": True,
                "disabledEvents": ["page_view", "button_click"],
                "piiMasking": True,
                "maxQueueSize": 100,
                "flushIntervalSeconds": 30,
                "batchSize": 10,
                "sinkConfigured": True
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.get_config()

            assert len(result.disabledEvents) == 2
            assert "page_view" in result.disabledEvents

    def test_get_config_headers_required(self, sdk):
        """Should include required header: x-shre-tenant"""
        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "trackingEnabled": True,
                "disabledEvents": [],
                "piiMasking": False,
                "maxQueueSize": 100,
                "flushIntervalSeconds": 30,
                "batchSize": 10,
                "sinkConfigured": True
            }
            mock_request.return_value = mock_response

            sdk.get_config()

            call_args = mock_request.call_args
            headers = call_args[1]['headers']
            assert headers['x-shre-tenant'] == 'test-workspace-123'

    def test_get_config_no_body_required(self, sdk):
        """Should use GET method with no request body"""
        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "trackingEnabled": True,
                "disabledEvents": [],
                "piiMasking": False,
                "maxQueueSize": 100,
                "flushIntervalSeconds": 30,
                "batchSize": 10,
                "sinkConfigured": True
            }
            mock_request.return_value = mock_response

            sdk.get_config()

            call_args = mock_request.call_args
            assert call_args[0][0] == "GET"

    def test_get_config_properties_alias(self, sdk):
        """Should provide snake_case property aliases"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "trackingEnabled": True,
                "disabledEvents": ["test"],
                "piiMasking": True,
                "maxQueueSize": 100,
                "flushIntervalSeconds": 30,
                "batchSize": 10,
                "sinkConfigured": True
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.get_config()

            # camelCase properties
            assert result.trackingEnabled is True
            assert result.disabledEvents == ["test"]
            assert result.piiMasking is True

            # snake_case aliases
            assert result.tracking_enabled is True
            assert result.disabled_events == ["test"]
            assert result.pii_masking is True

    def test_get_config_unauthorized_401(self, sdk):
        """Should raise Unauthorized on 401 response"""
        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Invalid tenant"
            mock_request.return_value = mock_response

            with pytest.raises(Unauthorized):
                sdk.get_config()

    def test_get_config_bad_request_400(self, sdk):
        """Should raise BadRequest on 400 response"""
        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Missing x-shre-tenant header"
            mock_request.return_value = mock_response

            with pytest.raises(BadRequest):
                sdk.get_config()

    def test_get_config_server_error_500(self, sdk):
        """Should raise ServerError on 5xx response"""
        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal server error"
            mock_request.return_value = mock_response

            with pytest.raises(ServerError):
                sdk.get_config()

    def test_get_config_network_error(self, sdk):
        """Should raise NetworkError on connection failure"""
        with patch.object(sdk.session, 'request') as mock_request:
            import requests
            mock_request.side_effect = requests.ConnectionError("Connection refused")

            with pytest.raises(NetworkError):
                sdk.get_config()


# ============================================================================
# MARK: - POST /v1/sdk/heartbeat Tests
# ============================================================================


class TestHeartbeatEndpoint:
    """Contract tests for POST /v1/sdk/heartbeat"""

    def test_send_heartbeat_success(self, sdk):
        """Should send heartbeat and receive server time"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {
                "ok": True,
                "serverTime": "2026-05-02T12:00:00Z"
            }
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.send_heartbeat(
                device_id="device_123",
                events_queued=5,
                events_sent=10
            )

            assert isinstance(result, HeartbeatResponse)
            assert result.ok is True
            assert result.serverTime == "2026-05-02T12:00:00Z"

    def test_send_heartbeat_default_events_sent(self, sdk):
        """Should default events_sent to 0 if not provided"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {"ok": True, "serverTime": "2026-05-02T12:00:00Z"}
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.send_heartbeat(
                device_id="device_123",
                events_queued=5
            )

            call_args = mock_request.call_args
            payload = call_args[1]['json']
            assert payload['eventsSent'] == 0

    def test_send_heartbeat_headers_required(self, sdk):
        """Should include required headers"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {"ok": True, "serverTime": "2026-05-02T12:00:00Z"}
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            sdk.send_heartbeat(
                device_id="device_123",
                events_queued=5
            )

            call_args = mock_request.call_args
            headers = call_args[1]['headers']
            assert headers['x-shre-tenant'] == 'test-workspace-123'
            assert headers['x-shre-app'] == 'python'

    def test_send_heartbeat_payload_fields(self, sdk):
        """Should include all payload fields in request"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {"ok": True, "serverTime": "2026-05-02T12:00:00Z"}
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            sdk.send_heartbeat(
                device_id="device_123",
                events_queued=5,
                events_sent=10
            )

            call_args = mock_request.call_args
            payload = call_args[1]['json']
            assert payload['tenantId'] == 'test-workspace-123'
            assert payload['app'] == 'python'
            assert payload['deviceId'] == 'device_123'
            assert payload['eventsQueued'] == 5
            assert payload['eventsSent'] == 10

    def test_send_heartbeat_zero_events(self, sdk):
        """Should accept zero events in queue"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {"ok": True, "serverTime": "2026-05-02T12:00:00Z"}
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.send_heartbeat(
                device_id="device_123",
                events_queued=0,
                events_sent=0
            )

            assert result.ok is True

    def test_send_heartbeat_properties_alias(self, sdk):
        """Should provide snake_case property aliases"""
        with patch.object(sdk.session, 'request') as mock_request:
            response_data = {"ok": True, "serverTime": "2026-05-02T12:00:00Z"}
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = response_data
            mock_request.return_value = mock_response

            result = sdk.send_heartbeat(
                device_id="device_123",
                events_queued=5
            )

            # camelCase property
            assert result.serverTime == "2026-05-02T12:00:00Z"
            # snake_case alias
            assert result.server_time == "2026-05-02T12:00:00Z"

    def test_send_heartbeat_bad_request_400(self, sdk):
        """Should raise BadRequest on 400 response"""
        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid payload"
            mock_request.return_value = mock_response

            with pytest.raises(BadRequest):
                sdk.send_heartbeat(
                    device_id="device_123",
                    events_queued=5
                )

    def test_send_heartbeat_unauthorized_401(self, sdk):
        """Should raise Unauthorized on 401 response"""
        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Invalid tenant"
            mock_request.return_value = mock_response

            with pytest.raises(Unauthorized):
                sdk.send_heartbeat(
                    device_id="device_123",
                    events_queued=5
                )

    def test_send_heartbeat_server_error_500(self, sdk):
        """Should raise ServerError on 5xx response"""
        with patch.object(sdk.session, 'request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 502
            mock_response.text = "Bad gateway"
            mock_request.return_value = mock_response

            with pytest.raises(ServerError):
                sdk.send_heartbeat(
                    device_id="device_123",
                    events_queued=5
                )

    def test_send_heartbeat_network_error(self, sdk):
        """Should raise NetworkError on connection failure"""
        with patch.object(sdk.session, 'request') as mock_request:
            import requests
            mock_request.side_effect = requests.Timeout("Request timed out")

            with pytest.raises(NetworkError):
                sdk.send_heartbeat(
                    device_id="device_123",
                    events_queued=5
                )


# ============================================================================
# MARK: - Integration Tests
# ============================================================================


class TestSDKIntegration:
    """Integration tests across multiple endpoints"""

    def test_full_workflow_read_mode(self, sdk):
        """Should complete read-only workflow: config + events"""
        with patch.object(sdk.session, 'request') as mock_request:
            # Mock config response
            config_response = Mock()
            config_response.status_code = 200
            config_response.json.return_value = {
                "trackingEnabled": True,
                "disabledEvents": [],
                "piiMasking": False,
                "maxQueueSize": 100,
                "flushIntervalSeconds": 30,
                "batchSize": 10,
                "sinkConfigured": True
            }

            # Mock events response
            events_response = Mock()
            events_response.status_code = 200
            events_response.json.return_value = {
                "accepted": 2,
                "rejected": 0,
                "trackingEnabled": True,
                "nextFlushSeconds": 30
            }

            mock_request.side_effect = [config_response, events_response]

            # Get config
            config = sdk.get_config()
            assert config.trackingEnabled is True

            # Send events
            events = [
                Event(event_id="evt_001", event_name="test1", entity_type="test"),
                Event(event_id="evt_002", event_name="test2", entity_type="test"),
            ]
            result = sdk.send_events_batch(events)
            assert result.accepted == 2

    def test_full_workflow_write_mode(self, sdk):
        """Should complete write workflow: session + heartbeat"""
        with patch.object(sdk.session, 'request') as mock_request:
            # Mock session response
            session_response = Mock()
            session_response.status_code = 200
            session_response.json.return_value = {
                "accessToken": "jwt_token_xyz",
                "expiresIn": 3600,
                "tokenType": "Bearer"
            }

            # Mock heartbeat response
            heartbeat_response = Mock()
            heartbeat_response.status_code = 200
            heartbeat_response.json.return_value = {
                "ok": True,
                "serverTime": "2026-05-02T12:00:00Z"
            }

            mock_request.side_effect = [session_response, heartbeat_response]

            # Create session
            session = sdk.create_session("pub_key_123")
            assert session.accessToken == "jwt_token_xyz"

            # Send heartbeat
            heartbeat = sdk.send_heartbeat("device_123", 5)
            assert heartbeat.ok is True

    def test_event_serialization(self):
        """Should properly serialize event to JSON"""
        now = datetime(2026, 5, 2, 12, 0, 0, tzinfo=timezone.utc)
        event = Event(
            event_id="evt_001",
            event_name="purchase",
            entity_type="transaction",
            entity_id="txn_123",
            timestamp=now,
            metadata={"amount": 99.99, "currency": "USD"}
        )

        serialized = event.to_dict()

        assert serialized["eventId"] == "evt_001"
        assert serialized["eventName"] == "purchase"
        assert serialized["entityType"] == "transaction"
        assert serialized["entityId"] == "txn_123"
        assert serialized["timestamp"] == "2026-05-02T12:00:00+00:00"
        assert serialized["metadata"]["amount"] == 99.99

    def test_event_without_optional_fields(self):
        """Should exclude optional fields when not provided"""
        event = Event(
            event_id="evt_001",
            event_name="test",
            entity_type="test"
        )

        serialized = event.to_dict()

        assert "entityId" not in serialized
        assert "timestamp" not in serialized
        assert "metadata" not in serialized
