# Shre AI SDK — Shared Spec (v2)

**Single source of truth.** Every language SDK (JS, Swift, Kotlin, Python, .NET) MUST implement this contract. Drift is forbidden — partner integration code is tested against this spec, not against any one SDK's docs.

## Hard rules

- **Zero or near-zero dependencies.** Use stdlib HTTP only. Edge / mobile / embedded POS targets — every kilobyte counts.
- **Single-file source where possible.** No build-tool frameworks. No heavy runtime.
- **Async-friendly but degrade to sync.** All public methods must work without an event loop on platforms that don't have one (e.g. older iOS).
- **No JWT library.** HS256 tokens are server-issued and treated opaquely client-side. Clients only verify they got a string and use it as `Authorization: Bearer <token>`.
- **No telemetry of the SDK itself.** Client error handling is `onError` callback — never silently send debug info to any host.

## Endpoints

| URL                                  | Plane   | Used by                                  |
| ------------------------------------ | ------- | ---------------------------------------- |
| `https://apiauth.shre.ai/v1/sdk/session`   | Control | Mint JWT (read_write) or fetch runtime config (read_only). Required on init. |
| `https://apiauth.shre.ai/v1/sdk/config`    | Control | Periodic kill-switch + disabled-events refresh (every 5 min).               |
| `https://events.shre.ai/v1/events/batch`   | Data    | Main ingest path. Batched events. Idempotent on `(tenant_id, event_id)`.    |
| `https://events.shre.ai/v1/sdk/heartbeat`  | Data    | Optional liveness ping with queue depth.                                    |

**Forbidden host:** any hostname that starts with `downloads.` — that's the SDK package mirror, not an API. Every SDK MUST refuse to initialize against `downloads.*` and explain in the error.

## Init contract

```
init({
  endpoint:        string  required   // e.g. "https://apiauth.shre.ai"
  eventsEndpoint:  string  optional   // defaults to endpoint
  tenantId:        string  required
  storeId:         string  optional
  userId:          string  optional
  role:            string  optional
  app:             string  required   // ^[a-z][a-z0-9_-]{0,31}$
  mode:            "read_only" | "read_write"   default "read_only"
  bootstrapKey:    string  required iff mode == "read_write"
  sdkVersion:      string  optional   // override; default from package
  flushIntervalSeconds: number  default 10  (server-tunable)
  batchSize:       number  default 50  (server-tunable)
  maxQueueSize:    number  default 5000
  timeoutMs:       number  default 8000
  onError:         (err, ctx) => void  optional
  onFlush:         (sent, failed) => void  optional
})
```

## Event envelope (canonical)

```
{
  "eventId":   "<client-uuid-v4>",
  "eventName": "<snake_or_camel, max 128 chars>",
  "entityType": "item" | "screen" | "tx" | ...,
  "entityId":   "<opaque>",
  "metadata":   { ... arbitrary JSON ... },
  "timestamp":  "<ISO 8601, optional — server fills if missing>"
}
```

Idempotency: server upserts on `(tenant_id, event_id)`. Retries are safe.

## HTTP headers (every request)

| Header                | Required when         | Value                                   |
| --------------------- | --------------------- | --------------------------------------- |
| `Content-Type`        | POST                  | `application/json`                      |
| `Authorization`       | mode = read_write     | `Bearer <jwt>`                          |
| `X-Shre-Tenant`       | always                | tenantId                                |
| `X-Shre-Store`        | optional              | storeId                                 |
| `X-Shre-App`          | always                | app                                     |
| `X-Shre-SDK-Version`  | always                | sdkVersion (e.g. `swift/2.0.0`)         |

## Failure handling matrix (client behavior)

| HTTP | Action                                                         |
| ---- | -------------------------------------------------------------- |
| 200  | Drain accepted events from queue                                |
| 401  | Re-bootstrap session (refresh JWT). One retry per failure.      |
| 403  | Set local kill-switch — stop tracking until next config refresh |
| 429  | Backoff: 5s → 15s → 30s → 60s → 300s. Don't drop events.        |
| 5xx  | Same backoff schedule. Events stay queued.                      |
| network offline | Stay queued. Flush on next interval after recovery.   |

## Local queue requirements

- **Max queue size:** `maxQueueSize` (default 5000). At cap, drop oldest.
- **Persistence:** SDKs targeting browser MUST persist via IndexedDB. Mobile MUST persist via SQLite/Core Data. Server-side SDKs MAY persist to disk (off by default).
- **Final drain:** SDK must attempt one last flush on `destroy()` AND on the platform's "about to terminate" hook (browser `beforeunload`, iOS `applicationWillTerminate`, Android `onTrimMemory(LEVEL_COMPLETE)`, Node `process.on('beforeExit')`, .NET `AppDomain.ProcessExit`).
- **Retry order:** failed batch goes back to the FRONT of the queue, preserving event order.

## SDK version string format

`<lang>/<semver>` — e.g. `js/2.0.0`, `swift/2.0.0`, `python/2.0.0`, `dotnet/2.0.0`, `kotlin/2.0.0`. Sent in `X-Shre-SDK-Version`. Used server-side for compatibility tracking.

## Edge / size budget

| Lang   | Max .min size  | Max deps     |
| ------ | -------------- | ------------ |
| JS     | 12 KB packed   | 0            |
| Swift  | 1 source file  | 0 (URLSession) |
| Kotlin | 1 source file  | 0 (HttpURLConnection) |
| Python | 1 source file  | 0 (urllib stdlib) |
| .NET   | 1 source file  | 0 (HttpClient stdlib) |
| REST   | OpenAPI spec   | n/a          |

## Conformance test (every SDK must pass)

A canonical fixture lives at `aros-developer-portal/sdks/contracts.test.json`. Each SDK MUST run it with the local relay-mock and produce identical request bodies + identical retry sequences. Drift between SDKs is a release blocker.
