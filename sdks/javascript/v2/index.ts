/**
 * @shreai/sdk v2 — POS / BOS learning-event SDK.
 *
 * Quick start (read-only, no API key):
 *
 *   import { ShreAI } from "@shreai/sdk";
 *
 *   ShreAI.init({
 *     endpoint:       "https://apiauth.shre.ai",     // control plane (session/config)
 *     eventsEndpoint: "https://events.shre.ai",      // data plane (events/heartbeat)
 *     tenantId: "merchant_123",
 *     storeId:  "store_001",
 *     userId:   "user_789",
 *     role:     "manager",
 *     app:      "rapid_bos",
 *     mode:     "read_only"        // default; no auth required
 *   });
 *
 *   ShreAI.trackEvent("price_updated", {
 *     entityType: "item", entityId: "UPC_012345678905",
 *     metadata: { oldValue: 10.49, newValue: 10.99 }
 *   });
 *
 * Read/write (server-to-server or trusted POS):
 *
 *   ShreAI.init({ ..., mode: "read_write", bootstrapKey: "<public_sdk_key>" });
 *
 * v2 differences from v1:
 *   - new endpoint shape: /v1/sdk/session, /v1/events/batch, /v1/sdk/config, /v1/sdk/heartbeat
 *   - read_only is anonymous (no Authorization header); read_write mints a JWT
 *   - every event carries a client-generated eventId for idempotency on retry
 *   - exponential backoff: 5 → 15 → 30 → 60 → 300 s
 *   - kill switch + disabled-events list pulled from /v1/sdk/config every 5 min
 *   - rejects endpoints whose hostname starts with `downloads.` (1033 trap)
 *   - flushes queue on destroy() and browser beforeunload
 */

// ─── Types ─────────────────────────────────────────────────────────────────

export type Mode = 'read_only' | 'read_write';
export type App = 'rapid_pos' | 'rapid_bos' | string;

export interface InitConfig {
  /** Auth + config plane (e.g. https://apiauth.shre.ai). Used for /v1/sdk/session and /v1/sdk/config. */
  endpoint: string;
  /** Optional dedicated data plane (e.g. https://events.shre.ai). Used for /v1/events/batch and /v1/sdk/heartbeat.
   *  If omitted, falls back to `endpoint`. Note: api.shre.ai serves API documentation, not the SDK control
   *  plane — pointing endpoint at api.shre.ai will return 404. */
  eventsEndpoint?: string;
  tenantId: string;
  storeId?: string;
  userId?: string;
  role?: string;
  app: App;
  mode?: Mode;
  /** Required only for mode: "read_write". A public bootstrap key issued by Shre AI. */
  bootstrapKey?: string;
  /** Override sdk version sent in headers (default read from package.json at build time) */
  sdkVersion?: string;
  /** Override fetch (React Native, Node 18-) */
  fetchFn?: typeof fetch;
  /** Initial flush interval in seconds (server may override) */
  flushIntervalSeconds?: number;
  /** Initial batch size (server may override) */
  batchSize?: number;
  /** Max events queued locally */
  maxQueueSize?: number;
  /** Per-request timeout */
  timeoutMs?: number;
  onError?: (err: Error, context: string) => void;
  onFlush?: (sent: number, failed: number) => void;
}

export interface TrackEventInput {
  entityType?: string;
  entityId?: string;
  metadata?: Record<string, unknown>;
  /** Override the canonical timestamp (default: now) */
  timestamp?: string;
}

export interface BatchAck {
  accepted: number;
  rejected: number;
  trackingEnabled: boolean;
  nextFlushSeconds: number;
  sinkReason?: string;
}

interface QueuedEvent {
  eventId: string;
  eventName: string;
  entityType?: string;
  entityId?: string;
  metadata: Record<string, unknown>;
  timestamp: string;
}

interface RemoteConfig {
  trackingEnabled: boolean;
  disabledEvents: string[];
  piiMasking: boolean;
  maxQueueSize: number;
  flushIntervalSeconds: number;
  batchSize: number;
}

interface SessionState {
  sdkToken: string | null;
  sessionId: string | null;
  expiresAt: number; // unix seconds
}

// ─── Internals ────────────────────────────────────────────────────────────

const SDK_VERSION = '2.0.0';
const RETRY_BACKOFF_S = [5, 15, 30, 60, 300];
const CONFIG_REFRESH_MS = 5 * 60_000;

function uuidv4(): string {
  // RFC4122 v4. Browser: crypto.randomUUID; Node: crypto.randomUUID; fallback: Math.random.
  const g = globalThis as unknown as { crypto?: { randomUUID?: () => string } };
  if (g.crypto?.randomUUID) return g.crypto.randomUUID();
  // Fallback (not crypto-strong, fine for dedup keys)
  let s = '';
  for (let i = 0; i < 36; i++) {
    if (i === 8 || i === 13 || i === 18 || i === 23) {
      s += '-';
    } else if (i === 14) {
      s += '4';
    } else if (i === 19) {
      s += ((Math.random() * 4) | (8 + 0)).toString(16);
    } else {
      s += ((Math.random() * 16) | 0).toString(16);
    }
  }
  return s;
}

class SDKImpl {
  private cfg!: InitConfig;
  private fetchFn!: typeof fetch;
  private baseUrl!: string;
  private eventsBaseUrl!: string;
  private session: SessionState = { sdkToken: null, sessionId: null, expiresAt: 0 };
  private queue: QueuedEvent[] = [];
  private inFlight = false;
  private retryAttempt = 0;
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private configTimer: ReturnType<typeof setInterval> | null = null;
  private remoteConfig: RemoteConfig = {
    trackingEnabled: true,
    disabledEvents: [],
    piiMasking: true,
    maxQueueSize: 5000,
    flushIntervalSeconds: 10,
    batchSize: 50,
  };
  private destroyed = false;
  private unloadHandlerBound = false;

  init(cfg: InitConfig): void {
    if (this.cfg) throw new Error('ShreAI: already initialized');
    if (!cfg.endpoint) throw new Error('ShreAI: endpoint is required');
    if (!cfg.tenantId) throw new Error('ShreAI: tenantId is required');
    if (!cfg.app) throw new Error('ShreAI: app is required');

    // Hostname guard: refuse downloads.* — that's a static asset host, not the API.
    try {
      const u = new URL(cfg.endpoint);
      if (/^downloads\./i.test(u.hostname)) {
        throw new Error(
          `ShreAI: endpoint hostname "${u.hostname}" looks like a download host. Use https://api.shre.ai instead.`,
        );
      }
    } catch (err) {
      if ((err as Error).message.startsWith('ShreAI:')) throw err;
      throw new Error(`ShreAI: invalid endpoint URL "${cfg.endpoint}"`);
    }

    this.cfg = { mode: 'read_only', ...cfg };
    const f = cfg.fetchFn || (typeof globalThis.fetch === 'function' ? globalThis.fetch.bind(globalThis) : undefined);
    if (!f) throw new Error('ShreAI: no fetch available — pass fetchFn for older Node/React Native');
    this.fetchFn = f;
    this.baseUrl = cfg.endpoint.replace(/\/$/, '');
    this.eventsBaseUrl = (cfg.eventsEndpoint || cfg.endpoint).replace(/\/$/, '');
    // Same hostname guard for events endpoint
    try {
      const u = new URL(this.eventsBaseUrl);
      if (/^downloads\./i.test(u.hostname)) {
        throw new Error(
          `ShreAI: eventsEndpoint hostname "${u.hostname}" looks like a download host. Use https://events.shre.ai or https://api.shre.ai instead.`,
        );
      }
    } catch (err) {
      if ((err as Error).message.startsWith('ShreAI:')) throw err;
      throw new Error(`ShreAI: invalid eventsEndpoint URL "${this.eventsBaseUrl}"`);
    }
    this.remoteConfig.flushIntervalSeconds = cfg.flushIntervalSeconds ?? 10;
    this.remoteConfig.batchSize = cfg.batchSize ?? 50;
    this.remoteConfig.maxQueueSize = cfg.maxQueueSize ?? 5000;

    // Bootstrap session (read_write blocks here; read_only just fetches initial config)
    this.bootstrap().catch((err) => this.cfg.onError?.(err, 'bootstrap'));

    // Auto-flush + remote-config refresh
    this.startTimers();
    this.bindUnload();
  }

  private async bootstrap(): Promise<void> {
    const body = {
      tenantId: this.cfg.tenantId,
      storeId: this.cfg.storeId,
      userId: this.cfg.userId,
      role: this.cfg.role,
      app: this.cfg.app,
      mode: this.cfg.mode,
      bootstrapKey: this.cfg.bootstrapKey,
      sdkVersion: this.cfg.sdkVersion || SDK_VERSION,
    };
    const res = await this.fetchFn(`${this.baseUrl}/v1/sdk/session`, {
      method: 'POST',
      headers: this.commonHeaders(),
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(this.cfg.timeoutMs ?? 8_000),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`ShreAI session failed ${res.status}: ${text.slice(0, 200)}`);
    }
    const data = (await res.json()) as {
      sdkToken: string | null;
      sessionId: string | null;
      trackingEnabled: boolean;
      mode: Mode;
      flushIntervalSeconds?: number;
      batchSize?: number;
      expiresIn?: number;
    };
    this.session = {
      sdkToken: data.sdkToken,
      sessionId: data.sessionId,
      expiresAt: Math.floor(Date.now() / 1000) + (data.expiresIn ?? 3600),
    };
    this.remoteConfig.trackingEnabled = data.trackingEnabled;
    this.remoteConfig.flushIntervalSeconds = data.flushIntervalSeconds ?? this.remoteConfig.flushIntervalSeconds;
    this.remoteConfig.batchSize = data.batchSize ?? this.remoteConfig.batchSize;
    // Also pull /sdk/config for kill-switch + disabled events
    await this.refreshRemoteConfig().catch(() => {});
  }

  private async refreshRemoteConfig(): Promise<void> {
    const res = await this.fetchFn(`${this.baseUrl}/v1/sdk/config`, {
      method: 'GET',
      headers: this.commonHeaders(),
      signal: AbortSignal.timeout(this.cfg.timeoutMs ?? 5_000),
    });
    if (!res.ok) return;
    const cfg = (await res.json()) as RemoteConfig;
    this.remoteConfig = { ...this.remoteConfig, ...cfg };
    // 403 disabled tracking is enforced inside batch; here just observe.
  }

  trackEvent(eventName: string, input: TrackEventInput = {}): void {
    if (this.destroyed || !this.cfg) return;
    if (!this.remoteConfig.trackingEnabled) return;
    if (this.remoteConfig.disabledEvents.includes(eventName)) return;
    const evt: QueuedEvent = {
      eventId: uuidv4(),
      eventName,
      entityType: input.entityType,
      entityId: input.entityId,
      metadata: input.metadata ?? {},
      timestamp: input.timestamp ?? new Date().toISOString(),
    };
    if (this.queue.length >= this.remoteConfig.maxQueueSize) {
      this.queue.shift(); // drop oldest
    }
    this.queue.push(evt);
  }

  trackScreen(name: string, metadata?: Record<string, unknown>): void {
    this.trackEvent('screen_viewed', { entityType: 'screen', entityId: name, metadata });
  }

  async flush(): Promise<BatchAck> {
    if (this.queue.length === 0) {
      return { accepted: 0, rejected: 0, trackingEnabled: this.remoteConfig.trackingEnabled, nextFlushSeconds: this.remoteConfig.flushIntervalSeconds };
    }
    if (this.inFlight) {
      return { accepted: 0, rejected: 0, trackingEnabled: this.remoteConfig.trackingEnabled, nextFlushSeconds: this.remoteConfig.flushIntervalSeconds };
    }
    this.inFlight = true;
    const batch = this.queue.splice(0, this.remoteConfig.batchSize);
    try {
      const ack = await this.postBatch(batch);
      this.retryAttempt = 0;
      this.cfg.onFlush?.(ack.accepted, ack.rejected);
      // Adapt local interval if server suggests one
      if (ack.nextFlushSeconds > 0 && ack.nextFlushSeconds !== this.remoteConfig.flushIntervalSeconds) {
        this.remoteConfig.flushIntervalSeconds = ack.nextFlushSeconds;
        this.restartFlushTimer();
      }
      return ack;
    } catch (err) {
      // Put events back at the FRONT, preserving order
      this.queue = batch.concat(this.queue).slice(0, this.remoteConfig.maxQueueSize);
      const e = err as Error & { status?: number };
      this.cfg.onError?.(e, 'flush');
      // Handle status-specific reactions
      if (e.status === 401) {
        // token may have expired — re-bootstrap once
        this.bootstrap().catch(() => {});
      } else if (e.status === 403) {
        this.remoteConfig.trackingEnabled = false;
      } else if (e.status === 429 || (e.status && e.status >= 500)) {
        this.scheduleBackoff();
      }
      this.cfg.onFlush?.(0, batch.length);
      return { accepted: 0, rejected: batch.length, trackingEnabled: this.remoteConfig.trackingEnabled, nextFlushSeconds: this.remoteConfig.flushIntervalSeconds };
    } finally {
      this.inFlight = false;
    }
  }

  private async postBatch(events: QueuedEvent[]): Promise<BatchAck> {
    // Refresh token if close to expiry (read_write only)
    if (this.cfg.mode === 'read_write' && this.session.expiresAt - Math.floor(Date.now() / 1000) < 60) {
      await this.bootstrap();
    }
    const res = await this.fetchFn(`${this.eventsBaseUrl}/v1/events/batch`, {
      method: 'POST',
      headers: this.commonHeaders(),
      body: JSON.stringify({ events }),
      signal: AbortSignal.timeout(this.cfg.timeoutMs ?? 8_000),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      const err = new Error(`batch ${res.status}: ${text.slice(0, 200)}`) as Error & { status: number };
      err.status = res.status;
      throw err;
    }
    return (await res.json()) as BatchAck;
  }

  async heartbeat(extras?: { deviceId?: string }): Promise<void> {
    if (!this.cfg) return;
    await this.fetchFn(`${this.eventsBaseUrl}/v1/sdk/heartbeat`, {
      method: 'POST',
      headers: this.commonHeaders(),
      body: JSON.stringify({
        tenantId: this.cfg.tenantId,
        storeId: this.cfg.storeId,
        app: this.cfg.app,
        deviceId: extras?.deviceId,
        sdkVersion: this.cfg.sdkVersion || SDK_VERSION,
        eventsQueued: this.queue.length,
      }),
      signal: AbortSignal.timeout(this.cfg.timeoutMs ?? 3_000),
    }).catch(() => {});
  }

  private commonHeaders(): Record<string, string> {
    const h: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Shre-Tenant': this.cfg.tenantId,
      'X-Shre-App': this.cfg.app,
      'X-Shre-SDK-Version': this.cfg.sdkVersion || SDK_VERSION,
    };
    if (this.cfg.storeId) h['X-Shre-Store'] = this.cfg.storeId;
    if (this.session.sdkToken) h['Authorization'] = `Bearer ${this.session.sdkToken}`;
    return h;
  }

  private scheduleBackoff(): void {
    const idx = Math.min(this.retryAttempt, RETRY_BACKOFF_S.length - 1);
    const delay = RETRY_BACKOFF_S[idx] * 1000;
    this.retryAttempt += 1;
    this.stopFlushTimer();
    setTimeout(() => {
      if (this.destroyed) return;
      this.flush().catch(() => {});
      this.startTimers();
    }, delay);
  }

  private startTimers(): void {
    this.restartFlushTimer();
    if (!this.configTimer) {
      this.configTimer = setInterval(() => {
        this.refreshRemoteConfig().catch(() => {});
      }, CONFIG_REFRESH_MS);
    }
  }

  private restartFlushTimer(): void {
    this.stopFlushTimer();
    const ms = Math.max(2_000, this.remoteConfig.flushIntervalSeconds * 1000);
    this.flushTimer = setInterval(() => {
      this.flush().catch(() => {});
    }, ms);
  }

  private stopFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
      this.flushTimer = null;
    }
  }

  private bindUnload(): void {
    if (this.unloadHandlerBound) return;
    if (typeof globalThis.addEventListener !== 'function') return;
    globalThis.addEventListener('beforeunload', () => {
      // best-effort sync flush via sendBeacon if available
      if (this.queue.length === 0) return;
      const g = globalThis as unknown as { navigator?: { sendBeacon?: (u: string, b: BodyInit) => boolean } };
      if (g.navigator?.sendBeacon) {
        const blob = new Blob([JSON.stringify({ events: this.queue })], { type: 'application/json' });
        g.navigator.sendBeacon(`${this.eventsBaseUrl}/v1/events/batch`, blob);
      } else {
        this.flush().catch(() => {});
      }
    });
    this.unloadHandlerBound = true;
  }

  async destroy(): Promise<void> {
    this.destroyed = true;
    this.stopFlushTimer();
    if (this.configTimer) {
      clearInterval(this.configTimer);
      this.configTimer = null;
    }
    // Final drain
    while (this.queue.length > 0) {
      const before = this.queue.length;
      const ack = await this.flush();
      if (ack.accepted === 0 || this.queue.length >= before) break; // give up if not draining
    }
  }

  getQueueSize(): number {
    return this.queue.length;
  }

  isReady(): boolean {
    return !!this.cfg && this.remoteConfig.trackingEnabled;
  }
}

// Singleton facade — apps typically only need one instance.
export const ShreAI = new SDKImpl();

// Also export the class for tests / multi-instance setups.
export { SDKImpl };
export { SDKImpl as ShreAIClient };
