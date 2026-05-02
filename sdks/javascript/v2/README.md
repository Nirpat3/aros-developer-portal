# @shreai/sdk v2

Learning-event SDK for Rapid POS / BOS (and any other application surface). Captures structured events, queues them locally, batches them to the Shre AI platform for fine-tuning + business intelligence.

## Install

```bash
npm install @shreai/sdk
```

## Quick start — read-only (default, no API key)

```ts
import { ShreAI } from "@shreai/sdk";

ShreAI.init({
  endpoint:        "https://api.shre.ai",     // auth/config plane (Mac)
  eventsEndpoint:  "https://events.shre.ai",  // hot data plane (Hostinger). Optional — falls back to endpoint.
  tenantId:        "merchant_123",
  storeId:         "store_001",
  userId:          "user_789",
  role:            "manager",
  app:             "rapid_bos",
  mode:            "read_only"                // default
});

// Do NOT use downloads.shre.ai for either — that's the SDK download host (Cloudflare Pages).
// The SDK refuses to initialize against `downloads.*` hostnames to prevent the 1033 trap.

// Track screen views
ShreAI.trackScreen("ItemEdit");

// Track structured events
ShreAI.trackEvent("price_updated", {
  entityType: "item",
  entityId:   "UPC_012345678905",
  metadata: { oldValue: 10.49, newValue: 10.99 }
});
```

## Read/write mode (opt-in, requires bootstrap key)

```ts
ShreAI.init({
  endpoint:     "https://api.shre.ai",
  tenantId:     "merchant_123",
  app:          "rapid_bos",
  mode:         "read_write",
  bootstrapKey: "<your_public_sdk_key>"   // request from Shre AI ops
});
```

In read/write mode the SDK calls `POST /v1/sdk/session` on init, swaps your bootstrap key for a short-lived JWT, and uses that on every subsequent batch upload. The bootstrap key never leaves the SDK as anything other than a hash.

## What's on the wire

```
ShreAI.trackEvent
       │
       ▼
local queue (max 5000, configurable)
       │  every flushIntervalSeconds (default 10s, server-tunable)
       ▼
POST  https://events.shre.ai/v1/events/batch                ← Hostinger relay (data plane)
   Authorization: Bearer <jwt>                               (read_write only)
   X-Shre-Tenant: <tenantId>   X-Shre-App: rapid_bos
   X-Shre-SDK-Version: 2.0.0
   { "events": [ { "eventId": "<uuid>", "eventName": "price_updated", ... } ] }
       │
       ▼
Hostinger VPS (shre-event-relay) → Supabase (sdk_events) → Shre brain learning loop


/v1/sdk/session and /v1/sdk/config still go to https://api.shre.ai (Mac plane).
```

## Endpoints used

| Verb  | Path                  | Auth                 | Why                                         |
| ----- | --------------------- | -------------------- | ------------------------------------------- |
| POST  | `/v1/sdk/session`     | bootstrapKey (rw)    | Mint short-lived JWT (rw) or fetch config   |
| GET   | `/v1/sdk/config`      | none                 | Kill switch, disabled events, runtime tunes |
| POST  | `/v1/events/batch`    | JWT (rw) / none (ro) | Main ingest path                            |
| POST  | `/v1/sdk/heartbeat`   | none                 | Liveness + queue depth (optional)           |

## Config knobs

```ts
ShreAI.init({
  // required
  endpoint, tenantId, app,

  // optional
  storeId, userId, role,
  mode: "read_only" | "read_write",          // default: read_only
  bootstrapKey,                              // required if mode = read_write
  flushIntervalSeconds: 10,                  // server may override
  batchSize: 50,                             // server may override
  maxQueueSize: 5000,
  timeoutMs: 8_000,
  fetchFn,                                   // for React Native or Node 18-

  onError: (err, ctx) => { /* … */ },
  onFlush: (sent, failed) => { /* … */ }
});
```

## Failure handling

| Status         | SDK reaction                                                |
| -------------- | ----------------------------------------------------------- |
| 401            | Re-bootstrap session (refresh JWT)                          |
| 403            | Disable tracking locally (kill switch)                      |
| 429            | Backoff: 5s → 15s → 30s → 60s → 5min                       |
| 5xx            | Same backoff schedule; events stay in local queue           |
| network offline| Events stay in queue until upload succeeds                  |

The SDK guarantees event ordering on retry. Every event has a client-generated `eventId` so the server upserts on conflict — your retries will not double-write.

## Browser support

Tested on Chrome / Safari / Firefox latest. Uses `navigator.sendBeacon` on `beforeunload` to drain the queue without blocking page navigation.

## Notes for partners

- Endpoint must be **`https://api.shre.ai`** (or your dedicated `https://*.shre.ai` partner host). The SDK refuses to initialize if the hostname starts with `downloads.` — that host serves SDK downloads only and will return Cloudflare error 1033.
- Bootstrap keys are tenant-scoped, hashed at rest in Supabase, and rotated by Shre AI ops. Treat them as public-on-client (they identify your install, not the user) but do not embed admin/service-role keys.
- Heartbeat is optional but recommended for support — it tells our health dashboard your SDK installs are alive even on quiet days.

## License

MIT
