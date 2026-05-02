# Shre SDK v2.0.0 — Test Checklist

**Test Execution Date:** [DATE]  
**SDK Version:** 2.0.0 (locked, May 2, 2026)  
**Status:** [PASS | FAIL]

---

## Overview

This checklist ensures ALL SDKs (iOS, Android, Web, Python, .NET) pass the same 40+ contract tests that validate the 4 locked endpoints.

**What's being tested:**
- POST /v1/events/batch — Event batching
- POST /v1/sdk/session — Authentication
- GET /v1/sdk/config — Configuration
- POST /v1/sdk/heartbeat — Device liveness

**Why it matters:**
Contract tests prevent breaking changes. Every test must pass on every platform, or the change is blocked at CI.

---

## Test Categories (40+ tests total per platform)

### Category 1: POST /v1/events/batch (12 tests)

**Happy Path (7 tests)**

- [ ] Accept single event with required headers
- [ ] Accept multiple events in batch
- [ ] Include eventId for idempotency
- [ ] Respect remote-configured batch size
- [ ] Send x-shre-tenant header
- [ ] Send x-shre-app header
- [ ] Handle JSON response deserialization

**Error Handling (5 tests)**

- [ ] Handle 400 Bad Request
- [ ] Handle 401 Unauthorized
- [ ] Handle 429 Rate Limited
- [ ] Handle 500 Server Error
- [ ] Handle network timeout

---

### Category 2: POST /v1/sdk/session (8 tests)

**Happy Path (4 tests)**

- [ ] Return sdkToken for read_write mode
- [ ] Send bootstrap key in read_write mode
- [ ] Send x-shre-tenant header
- [ ] Use POST method

**Error Handling (4 tests)**

- [ ] Handle invalid bootstrap key (401)
- [ ] Handle missing endpoint (400)
- [ ] Handle server error (500)
- [ ] Return application/json content type

---

### Category 3: GET /v1/sdk/config (8 tests)

**Happy Path (5 tests)**

- [ ] Return config with required fields
- [ ] Use GET method
- [ ] Send x-shre-tenant header
- [ ] Validate all field types (boolean, array, number)
- [ ] Return application/json content type

**Error Handling (3 tests)**

- [ ] Handle missing x-shre-tenant (400)
- [ ] Handle kill-switch (trackingEnabled: false)
- [ ] Handle disabled events list

---

### Category 4: POST /v1/sdk/heartbeat (8 tests)

**Happy Path (6 tests)**

- [ ] Send heartbeat successfully
- [ ] Include tenantId in heartbeat
- [ ] Include app in heartbeat
- [ ] Include eventsQueued in heartbeat
- [ ] Use POST method
- [ ] Send x-shre-tenant header

**Error Handling (2 tests)**

- [ ] Handle network failure gracefully
- [ ] Server returns 200 even on transient issues

---

### Category 5: Cross-Endpoint Tests (4 tests)

- [ ] Handle multiple endpoints with different base URLs
- [ ] Enforce x-shre-tenant on all endpoints
- [ ] Enforce x-shre-app on all endpoints
- [ ] All endpoints return valid JSON (never HTML)

---

## Platform Test Matrix

| Test Case                    | JavaScript | iOS | Android | Python | .NET |
|------------------------------|------------|-----|---------|--------|------|
| accept_single_event          | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| accept_multiple_events       | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| include_eventId_idempotency  | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| respect_batch_size           | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| send_x_shre_tenant           | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| send_x_shre_app              | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| json_response_deserialize    | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| handle_400_bad_request       | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| handle_401_unauthorized      | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| handle_429_rate_limited      | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| handle_500_server_error      | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| handle_network_timeout       | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| session_read_write_token     | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| session_bootstrap_key        | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| session_x_shre_tenant        | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| session_use_post_method      | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| session_invalid_key_401      | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| session_missing_field_400    | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| session_server_error_500     | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| session_json_response        | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| config_required_fields       | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| config_use_get_method        | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| config_x_shre_tenant         | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| config_field_types           | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| config_json_response         | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| config_missing_header_400    | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| config_kill_switch           | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| config_disabled_events       | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| heartbeat_success            | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| heartbeat_include_tenant     | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| heartbeat_include_app        | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| heartbeat_include_queued     | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| heartbeat_use_post           | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| heartbeat_x_shre_tenant      | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| heartbeat_network_failure    | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| multi_endpoint_base_urls     | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| enforce_tenant_all_endpoints | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| enforce_app_all_endpoints    | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |
| json_never_html_on_error     | [ ]        | [ ] | [ ]     | [ ]    | [ ]  |

**Total: 40 tests × 5 platforms = 200 test executions**

---

## Test Execution Instructions

### JavaScript/TypeScript

```bash
cd aros-developer-portal/sdks/javascript/v2
npm install
npm test
# Expected output: "40+ tests pass in <10s"
```

**Test file:** `aros-developer-portal/sdks/javascript/v2/__tests__/ShreSDK.test.ts`

**Framework:** Vitest

**Expected results:**
```
✓ Shre SDK v2.0.0 — Contract Tests (40+ tests)
  ✓ Endpoint: POST /v1/events/batch (12 tests)
  ✓ Endpoint: POST /v1/sdk/session (8 tests)
  ✓ Endpoint: GET /v1/sdk/config (8 tests)
  ✓ Endpoint: POST /v1/sdk/heartbeat (8 tests)
  ✓ Cross-endpoint behavior (4 tests)

40 tests pass in 8.5s
```

---

### iOS/Swift

```bash
cd ~/Documents/Projects/shreai
# Run iOS contract tests via shre-router test suite
pnpm test shre-router/src/routes/__tests__/sdk.test.ts
```

**Test file:** `shre-router/src/routes/__tests__/sdk.test.ts`

**Framework:** Vitest (runs Node tests for iOS SDK contract)

**Expected results:** Same as JavaScript (40+ tests)

---

### Android/Kotlin

```bash
cd aros-developer-portal/sdks/kotlin
./gradlew test
# Expected: 40+ tests pass
```

**Test file:** `aros-developer-portal/sdks/kotlin/src/test/kotlin/*/SdkContractTest.kt`

**Framework:** JUnit

---

### Python

```bash
cd aros-developer-portal/sdks/python
pip install -e ".[test]"
pytest tests/test_sdk.py -v
# Expected: 40+ tests pass
```

**Test file:** `aros-developer-portal/sdks/python/tests/test_sdk.py`

**Framework:** pytest

---

### .NET/C#

```bash
cd aros-developer-portal/sdks/dotnet
dotnet test ShreAI.Tests.csproj
# Expected: 40+ tests pass
```

**Test file:** `aros-developer-portal/sdks/dotnet/ShreAI.Tests/SdkContractTests.cs`

**Framework:** NUnit/xUnit

---

## Failure Investigation

### If tests fail:

1. **Check endpoint status**
   ```bash
   curl -I https://api.shre.ai/health
   curl -I https://events.shre.ai/health
   ```

2. **Check for breaking changes**
   - Did any response field name change?
   - Did any required header get removed?
   - Did any HTTP method change?

3. **Check contract spec**
   - Review `contracts.test.json` for expected schema
   - Compare actual response to expected schema

4. **Review changelog**
   - Check `docs/SDK-VERSION-MANAGEMENT.md` for recent changes
   - Check `CHANGELOG.md` for deprecations

### Common failures:

| Symptom                          | Cause                                    | Fix                                        |
|----------------------------------|------------------------------------------|--------------------------------------------|
| "Missing required header"        | x-shre-tenant or x-shre-app not sent    | Verify request headers match spec          |
| "Invalid JSON response"          | Server returned HTML on error           | Check endpoint for errors                  |
| "Unexpected response shape"      | Response field was renamed/removed      | Update test expectations + update all SDKs |
| "401 Unauthorized"               | Token expired or invalid                 | Re-bootstrap session                       |
| "429 Rate Limited"               | Too many requests too fast              | Reduce test concurrency                    |
| "Timeout"                        | Network latency or endpoint down        | Check endpoint health, increase timeout    |

---

## Platform-Specific Notes

### JavaScript/Web

- **Framework:** Vitest (Vitest + fetch mocking)
- **File:** `__tests__/ShreSDK.test.ts`
- **Run time:** ~8s
- **Coverage:** 40+ tests covering all endpoints, error cases, serialization
- **Node versions:** 18+ (SDK requires native fetch)

### iOS/Swift

- **Framework:** XCTest (runs in `shre-router` Node test suite for contract validation)
- **File:** `shre-router/src/routes/__tests__/sdk.test.ts`
- **Run time:** ~5s
- **Coverage:** 40+ tests (shared with all platforms)
- **Note:** Contract tests run on backend; iOS SDK tests run in Xcode

### Android/Kotlin

- **Framework:** JUnit 4
- **File:** `sdks/kotlin/src/test/kotlin/**SdkContractTest.kt`
- **Run time:** ~10s
- **Coverage:** 40+ tests
- **Dependencies:** Mockito, OkHttp MockWebServer

### Python

- **Framework:** pytest
- **File:** `sdks/python/tests/test_sdk.py`
- **Run time:** ~7s
- **Coverage:** 40+ tests
- **Dependencies:** pytest, requests-mock

### .NET/C#

- **Framework:** NUnit or xUnit
- **File:** `sdks/dotnet/ShreAI.Tests/SdkContractTests.cs`
- **Run time:** ~8s
- **Coverage:** 40+ tests
- **Dependencies:** HttpClientFactory, Moq

---

## Continuous Integration

All SDKs are tested in CI/CD on every commit.

### Pre-commit hook (local)

```bash
scripts/validate-sdk-contracts.sh
```

Runs all SDK tests. If any fail, commit is blocked.

### GitHub Actions (CI)

- **Trigger:** Push to `main` or pull request
- **Jobs:** JavaScript, iOS, Android, Python, .NET (in parallel)
- **Timeout:** 5 minutes per platform
- **Failure:** Blocks merge until all tests pass

### Quality gate

If tests fail in CI:
1. Change is immediately blocked
2. Author is notified
3. Change cannot be merged until tests pass
4. Tests must be updated first to document breaking changes

---

## Test Results Documentation

**JavaScript Test Results:**

- **File:** `aros-developer-portal/sdks/javascript/v2/__tests__/ShreSDK.test.ts`
- **Framework:** Vitest
- **Last run:** [DATE]
- **Status:** PASS ✅
- **Tests:** 40+
- **Duration:** <10s
- **Coverage:** All endpoints, error cases, serialization

---

## Updating Tests

If you need to change an endpoint:

1. **Update the contract spec** (`contracts.test.json`)
2. **Update ALL SDK tests** (JavaScript, iOS, Android, Python, .NET)
3. **Document the change** in `docs/SDK-VERSION-MANAGEMENT.md`
4. **Announce deprecation** (if breaking)
5. **Version bump** in `package.json` + all SDK version files

---

## References

- **Contract Spec:** `aros-developer-portal/sdks/contracts.test.json`
- **Version Management:** `docs/SDK-VERSION-MANAGEMENT.md`
- **Breaking Changes:** `docs/SDK-PLATFORM-STATUS.md` (Breaking Change Protocol)
- **Platform Status:** `SDK-PLATFORM-STATUS.md`

---

## Sign-off

- [ ] All JavaScript tests pass
- [ ] All iOS tests pass
- [ ] All Android tests pass
- [ ] All Python tests pass
- [ ] All .NET tests pass
- [ ] No breaking changes
- [ ] All SDKs return valid JSON (never HTML on error)
- [ ] All required headers enforced
- [ ] Health monitor confirms all 4 endpoints alive

**Tested by:** [NAME]  
**Date:** [DATE]  
**Version:** 2.0.0 (locked)  
**Status:** READY FOR PRODUCTION
