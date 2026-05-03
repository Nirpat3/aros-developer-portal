# ShreAI iOS SDK v2.0.0

**Production Ready — API Contract Locked**

> **Standalone repo for SPM install:** https://github.com/Shreai/sdk-swift
> Add via Xcode → File → Add Package Dependencies → `https://github.com/Shreai/sdk-swift.git`
> This directory remains the canonical source; the standalone repo is mirrored from here.

---

## Quick Start

### Installation (Swift Package Manager)

Add to your `Package.swift`:

```swift
dependencies: [
    .package(url: "https://github.com/Nirpat3/aros-developer-portal.git", branch: "main")
]
```

Or in Xcode: File → Add Packages → Enter URL above

### Basic Usage

```swift
import ShreAI

// Initialize SDK
let sdk = ShreSDK(
    tenantId: "client-123",
    platform: "ios"
)

// Send events
sdk.sendEventsBatch(events: [
    Event(
        eventId: UUID().uuidString,
        eventName: "app_launch",
        entityType: "app"
    )
]) { result in
    switch result {
    case .success(let response):
        print("Accepted: \(response.accepted)")
    case .failure(let error):
        print("Error: \(error.localizedDescription)")
    }
}
```

---

## Features

| Feature | Status | Details |
|---------|--------|---------|
| **Read-Only Mode** | ✓ | No auth required, for analytics capture |
| **Read-Write Mode** | ✓ | JWT authentication, requires bootstrap key |
| **Event Batching** | ✓ | Send up to 100 events per batch |
| **Configuration** | ✓ | Per-tenant settings (flush interval, batch size) |
| **Liveness Tracking** | ✓ | Heartbeat signal with queue depth |

---

## API Reference

### `sendEventsBatch(events:completion:)`

Send analytics events (read-only mode).

```swift
sdk.sendEventsBatch(events: events) { result in
    switch result {
    case .success(let response):
        // response.accepted: Int
        // response.rejected: Int
        // response.trackingEnabled: Bool
        // response.nextFlushSeconds: Int
    case .failure(let error):
        // Handle ShreError
    }
}
```

### `createSession(bootstrapKey:completion:)`

Mint JWT for read-write access.

```swift
sdk.createSession(bootstrapKey: "your-key") { result in
    switch result {
    case .success(let response):
        // response.accessToken: String (JWT)
        // response.expiresIn: Int (seconds)
        // response.tokenType: "Bearer"
    case .failure(let error):
        // Handle ShreError
    }
}
```

### `getConfig(completion:)`

Fetch per-tenant configuration.

```swift
sdk.getConfig() { result in
    switch result {
    case .success(let config):
        // config.trackingEnabled: Bool
        // config.disabledEvents: [String]
        // config.flushIntervalSeconds: Int
        // config.batchSize: Int
    case .failure(let error):
        // Handle ShreError
    }
}
```

### `sendHeartbeat(deviceId:eventsQueued:eventsSent:completion:)`

Send device liveness signal.

```swift
sdk.sendHeartbeat(
    deviceId: UIDevice.current.identifierForVendor?.uuidString ?? "unknown",
    eventsQueued: queueCount,
    eventsSent: sentCount
) { result in
    switch result {
    case .success(let response):
        // response.ok: Bool
        // response.serverTime: String (ISO 8601)
    case .failure(let error):
        // Handle ShreError
    }
}
```

---

## Data Models

### Event

```swift
Event(
    eventId: String,           // UUID for deduplication
    eventName: String,         // e.g., "purchase", "app_launch"
    entityType: String,        // e.g., "transaction", "app"
    entityId: String? = nil,   // e.g., UPC, product ID
    timestamp: Date? = nil,    // Defaults to now
    metadata: [String: Any]? = nil  // Custom context
)
```

### EventsResponse

```swift
struct EventsResponse {
    let accepted: Int           // Events accepted
    let rejected: Int           // Events rejected
    let trackingEnabled: Bool   // Whether tracking is active
    let nextFlushSeconds: Int   // Recommended flush interval
}
```

### SessionResponse

```swift
struct SessionResponse {
    let accessToken: String     // JWT token
    let expiresIn: Int          // Expiry in seconds
    let tokenType: String       // Always "Bearer"
}
```

### ConfigResponse

```swift
struct ConfigResponse {
    let trackingEnabled: Bool
    let disabledEvents: [String]
    let piiMasking: Bool
    let maxQueueSize: Int
    let flushIntervalSeconds: Int
    let batchSize: Int
    let sinkConfigured: Bool
}
```

### HeartbeatResponse

```swift
struct HeartbeatResponse {
    let ok: Bool
    let serverTime: String      // ISO 8601 timestamp
}
```

---

## Error Handling

All endpoints return `ShreError` on failure:

```swift
enum ShreError: Error, LocalizedError {
    case networkError(Error)           // Network failure
    case invalidResponse               // Malformed response
    case noData                        // Empty response
    case badRequest                    // 400 — missing headers
    case unauthorized                  // 401 — invalid JWT
    case serverError(Int)              // 5xx — server error
    case unknownError(Int)             // Other HTTP errors
    case decodingError(Error)          // JSON parsing error
}
```

---

## Best Practices

### 1. Initialize Once

```swift
class AppDelegate: UIResponder, UIApplicationDelegate {
    static let shre = ShreSDK(tenantId: "your-tenant-id")
}
```

### 2. Batch Events

Don't send individual events. Collect and batch:

```swift
var eventQueue: [Event] = []

func trackEvent(_ event: Event) {
    eventQueue.append(event)
    if eventQueue.count >= 50 {
        flushEvents()
    }
}

func flushEvents() {
    AppDelegate.shre.sendEventsBatch(events: eventQueue) { result in
        if case .success = result {
            self.eventQueue.removeAll()
        }
    }
}
```

### 3. Send Heartbeat Periodically

```swift
Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { _ in
    AppDelegate.shre.sendHeartbeat(
        deviceId: UIDevice.current.identifierForVendor?.uuidString ?? "unknown",
        eventsQueued: eventQueue.count
    ) { _ in }
}
```

### 4. Handle Network Failures Gracefully

```swift
sdk.sendEventsBatch(events: events) { result in
    switch result {
    case .success(let response):
        if !response.trackingEnabled {
            // Tracking disabled, stop sending
            stopTracking()
        }
    case .failure(let error):
        // Retry with exponential backoff
        self.scheduleRetry(after: 60)
    }
}
```

---

## Headers Reference

### Required Headers

| Header | Value | Example |
|--------|-------|---------|
| `x-shre-tenant` | Tenant ID | `client-123` |
| `x-shre-app` | Platform | `ios` |

### Optional Headers

| Header | Value | Use |
|--------|-------|-----|
| `Authorization` | Bearer JWT | For read-write mode |

---

## Contract & Support

- **Contract Date:** May 2, 2026
- **Status:** Locked (no breaking changes until May 2, 2027)
- **Deprecation Window:** 6 months for breaking changes
- **API Docs:** https://api.shre.ai (OpenAPI 3.0)
- **Support:** support@shre.ai

---

## Changelog

### v2.0.0 (May 2, 2026)
- Initial stable release
- All 4 endpoints locked
- 6-month backward compatibility guarantee
