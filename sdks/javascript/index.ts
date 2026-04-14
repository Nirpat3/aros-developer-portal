/**
 * @aros/pos-sdk — Connect any POS system to the AROS AI platform.
 *
 * Zero dependencies. Works in Node.js, React Native, Electron, or browser.
 *
 * Quick start:
 *   import { createArosPOS } from "@aros/pos-sdk";
 *
 *   const pos = createArosPOS({
 *     endpoint: "https://your-shre-instance.com",
 *     tenantId: "store-42",
 *     vendor: "verifone-commander",
 *     deviceId: "REG-001",
 *     apiKey: "your-api-key",
 *   });
 *
 *   // Register your device
 *   await pos.register({ model: "Commander 2.0", firmware: "4.1.2" });
 *
 *   // Send events as they happen
 *   pos.itemScanned({ barcode: "012345", description: "Fireball 750ml", price: 14.99 });
 *   pos.transactionComplete({ total: 42.50, paymentType: "credit", itemCount: 3 });
 *   pos.voidLine({ itemId: "item-1", reason: "customer_changed_mind" });
 *
 *   // Get AI recommendations
 *   const recs = await pos.getRecommendations("item-123");
 *   const quickOrder = await pos.getQuickOrder("loyalty-456");
 *   const messages = await pos.getMessages();
 */

// ── Types ───────────────────────────────────────────────────────────────────

export type PosVendor =
  | 'mobilepos'
  | 'verifone-commander'
  | 'verifone-ruby'
  | 'ncr-aloha'
  | 'ncr-counterpoint'
  | 'ncr-voyix'
  | 'gilbarco-passport'
  | 'gilbarco-flexpay'
  | 'wayne-fusion'
  | 'oracle-simphony'
  | 'clover'
  | 'square'
  | 'toast'
  | 'lightspeed'
  | 'shopify-pos'
  | 'generic'
  | `custom-${string}`;

export interface ArosPOSConfig {
  /** Shre platform URL (e.g. "http://127.0.0.1:5497" or "https://api.shre.ai") */
  endpoint: string;
  /** Your store/tenant identifier */
  tenantId: string;
  /** POS vendor type */
  vendor: PosVendor;
  /** Unique device/register identifier */
  deviceId: string;
  /** API key for authentication (optional for local installs) */
  apiKey?: string;
  /** Request timeout in ms (default: 10000) */
  timeoutMs?: number;
  /** Enable offline queue (default: true) */
  offlineQueue?: boolean;
  /** Max events in offline queue (default: 500) */
  maxQueueSize?: number;
  /** Auto-flush interval in ms (default: 30000) */
  flushIntervalMs?: number;
  /** Custom fetch implementation (for React Native or environments without global fetch) */
  fetchFn?: typeof fetch;
  /** Called when an event fails to send (for custom error handling) */
  onError?: (error: Error, event: ConnexusEvent) => void;
  /** Called when offline queue is flushed */
  onFlush?: (count: number, success: boolean) => void;
}

export interface ConnexusEvent {
  vendor: string;
  eventType: string;
  data: Record<string, unknown>;
  deviceId?: string;
  tenantId?: string;
  timestamp?: string;
}

export interface ItemData {
  barcode?: string;
  itemId?: string;
  description?: string;
  price?: number;
  quantity?: number;
  department?: string;
  itemType?: string;
  isRefund?: boolean;
  isEBT?: boolean;
  [key: string]: unknown;
}

export interface TransactionData {
  transactionId?: string;
  total?: number;
  subtotal?: number;
  tax?: number;
  itemCount?: number;
  paymentType?: string;
  cashierName?: string;
  registerID?: string;
  items?: ItemData[];
  [key: string]: unknown;
}

export interface VoidData {
  transactionId?: string;
  itemId?: string;
  reason?: string;
  amount?: number;
  cashierName?: string;
  [key: string]: unknown;
}

export interface DiscountData {
  itemId?: string;
  discountType?: string;
  amount?: number;
  scope?: 'item' | 'transaction';
  [key: string]: unknown;
}

export interface PriceOverrideData {
  itemId?: string;
  originalPrice?: number;
  newPrice?: number;
  reason?: string;
  cashierName?: string;
  [key: string]: unknown;
}

export interface CustomerData {
  customerId?: string;
  loyaltyNumber?: string;
  customerName?: string;
  loyaltyTier?: string;
  [key: string]: unknown;
}

export interface FuelData {
  pumpNumber?: string;
  fuelGrade?: string;
  gallons?: number;
  total?: number;
  [key: string]: unknown;
}

export interface Recommendation {
  target_item: string;
  target_description: string;
  target_department: string;
  target_price: number;
  co_purchase_count: number;
  confidence: number;
  source: string;
}

export interface CashierMessage {
  id: string;
  type: string;
  title: string;
  body?: string;
  priority: number;
  source: string;
  created_at: string;
  expires_at?: string;
}

export interface QuickOrderItem {
  item_id: string;
  description: string;
  department: string;
  price: number;
  purchase_count: number;
  last_purchased: string;
}

export interface PosAnalytics {
  period: { minutes: number; since: string };
  scans: number;
  transactions: number;
  totalRevenue: number;
  avgTicket: number;
  events: Record<string, number>;
  alerts: {
    voids: number;
    refunds: number;
    noSales: number;
    priceOverrides: number;
  };
}

// ── SDK Interface ───────────────────────────────────────────────────────────

export interface ArosPOS {
  // ── Device Management ──
  /** Register this device with the AROS platform */
  register(info?: {
    model?: string;
    firmware?: string;
    protocolVersion?: string;
    capabilities?: string[];
  }): Promise<{ ok: boolean; message: string }>;

  // ── Event Emission (fire-and-forget, queues offline) ──
  /** Item scanned / added to cart */
  itemScanned(item: ItemData): void;
  /** Item quantity changed */
  quantityChanged(item: ItemData & { direction: 'PLUS' | 'MINUS'; newQuantity: number }): void;
  /** Transaction completed (sale) */
  transactionComplete(txn: TransactionData): void;
  /** Void a line item or entire transaction */
  voidLine(data: VoidData): void;
  voidTransaction(data: VoidData): void;
  /** Return / refund */
  returnItem(data: VoidData): void;
  /** Discount applied */
  discountApplied(data: DiscountData): void;
  /** Price override */
  priceOverride(data: PriceOverrideData): void;
  /** No-sale / drawer opened */
  noSale(data?: { reason?: string; cashierName?: string }): void;
  /** Customer identified (loyalty swipe) */
  customerIdentified(data: CustomerData): void;
  /** Fuel dispensed */
  fuelDispensed(data: FuelData): void;
  /** Send any custom event */
  sendEvent(eventType: string, data: Record<string, unknown>): void;
  /** Send a batch of completed basket items (teaches co-purchase associations) */
  learnBasket(
    items: ItemData[],
    customerId?: string,
  ): Promise<{ ok: boolean; associationsCreated: number }>;

  // ── AI Intelligence (async, requires network) ──
  /** Get upsell/cross-sell recommendations for an item */
  getRecommendations(itemId: string, limit?: number): Promise<Recommendation[]>;
  /** Get customer's frequent items for quick ring-up */
  getQuickOrder(customerId: string, limit?: number): Promise<QuickOrderItem[]>;
  /** Get pending cashier messages/alerts */
  getMessages(): Promise<CashierMessage[]>;
  /** Acknowledge a cashier message */
  ackMessage(messageId: string): Promise<void>;
  /** Get real-time POS analytics */
  getAnalytics(minutes?: number): Promise<PosAnalytics>;

  // ── Queue Management ──
  /** Flush offline event queue (called automatically on interval) */
  flush(): Promise<{ sent: number; failed: number }>;
  /** Get current queue size */
  getQueueSize(): number;
  /** Start auto-flush interval */
  startAutoFlush(): void;
  /** Stop auto-flush interval */
  stopAutoFlush(): void;
  /** Destroy the SDK instance (stops timers, clears queue) */
  destroy(): void;
}

// ── Implementation ──────────────────────────────────────────────────────────

export function createArosPOS(config: ArosPOSConfig): ArosPOS {
  const {
    endpoint,
    tenantId,
    vendor,
    deviceId,
    apiKey,
    timeoutMs = 10_000,
    offlineQueue = true,
    maxQueueSize = 500,
    flushIntervalMs = 30_000,
    onError,
    onFlush,
  } = config;

  // Use provided fetch or global
  const _fetch =
    config.fetchFn || (typeof globalThis.fetch === 'function' ? globalThis.fetch : null);
  if (!_fetch) {
    throw new Error(
      '@aros/pos-sdk: No fetch available. Pass fetchFn in config for React Native or older Node.js.',
    );
  }

  const baseUrl = endpoint.replace(/\/$/, '');
  let _queue: ConnexusEvent[] = [];
  let _flushTimer: ReturnType<typeof setInterval> | null = null;

  // ── HTTP helpers ────────────────────────────────────────────────────────

  function headers(): Record<string, string> {
    const h: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Tenant-Id': tenantId,
      'X-Device-Id': deviceId,
      'X-POS-Vendor': vendor,
    };
    if (apiKey) h['Authorization'] = `Bearer ${apiKey}`;
    return h;
  }

  async function post<T = unknown>(path: string, body: unknown): Promise<T> {
    const res = await _fetch!(`${baseUrl}${path}`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`AROS API ${res.status}: ${text}`);
    }
    return res.json() as Promise<T>;
  }

  async function get<T = unknown>(path: string): Promise<T> {
    const res = await _fetch!(`${baseUrl}${path}`, {
      method: 'GET',
      headers: headers(),
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`AROS API ${res.status}: ${text}`);
    }
    return res.json() as Promise<T>;
  }

  // ── Queue management ────────────────────────────────────────────────────

  function enqueue(event: ConnexusEvent): void {
    if (!offlineQueue) {
      // Fire and forget — send immediately, ignore errors
      post('/v1/connexus/ingest', event).catch((err) => {
        onError?.(err, event);
      });
      return;
    }

    _queue.push(event);
    if (_queue.length > maxQueueSize) {
      _queue.shift(); // Drop oldest
    }
  }

  async function flush(): Promise<{ sent: number; failed: number }> {
    if (_queue.length === 0) return { sent: 0, failed: 0 };

    const batch = [..._queue];
    _queue = [];

    try {
      await post('/v1/connexus/ingest', { events: batch });
      onFlush?.(batch.length, true);
      return { sent: batch.length, failed: 0 };
    } catch (err) {
      // Put events back at the front of the queue
      _queue = [...batch, ..._queue].slice(0, maxQueueSize);
      onFlush?.(0, false);
      return { sent: 0, failed: batch.length };
    }
  }

  // ── Event builders ──────────────────────────────────────────────────────

  function makeEvent(eventType: string, data: Record<string, unknown>): ConnexusEvent {
    return {
      vendor,
      eventType,
      data,
      deviceId,
      tenantId,
      timestamp: new Date().toISOString(),
    };
  }

  // ── Public API ──────────────────────────────────────────────────────────

  const sdk: ArosPOS = {
    // Device
    async register(info = {}) {
      return post('/v1/connexus/register', {
        deviceId,
        tenantId,
        vendor,
        model: info.model,
        firmware: info.firmware,
        protocolVersion: info.protocolVersion || '1.0',
        capabilities: info.capabilities,
      });
    },

    // Events
    itemScanned(item) {
      enqueue(makeEvent('ItemSale', item));
    },

    quantityChanged(item) {
      enqueue(
        makeEvent('item_sale', {
          ...item,
          event: 'qty_change',
        }),
      );
    },

    transactionComplete(txn) {
      enqueue(makeEvent('TransactionComplete', txn));
      // Auto-learn basket associations if items provided
      if (txn.items && txn.items.length >= 2) {
        sdk.learnBasket(txn.items).catch(() => {});
      }
    },

    voidLine(data) {
      enqueue(makeEvent('VoidLine', { ...data, lineItem: true }));
    },

    voidTransaction(data) {
      enqueue(makeEvent('VoidTransaction', data));
    },

    returnItem(data) {
      enqueue(makeEvent('Return', data));
    },

    discountApplied(data) {
      enqueue(makeEvent('Discount', data));
    },

    priceOverride(data) {
      enqueue(makeEvent('PriceOverride', data));
    },

    noSale(data = {}) {
      enqueue(makeEvent('NoSale', data));
    },

    customerIdentified(data) {
      enqueue(makeEvent('LoyaltySwipe', data));
    },

    fuelDispensed(data) {
      enqueue(makeEvent('FuelDispense', data));
    },

    sendEvent(eventType, data) {
      enqueue(makeEvent(eventType, data));
    },

    async learnBasket(items, customerId) {
      return post('/v1/connexus/ingest/learn', {
        items: items.map((i) => ({
          itemId: i.itemId || i.barcode || '',
          description: i.description || '',
          department: i.department || '',
          price: i.price || 0,
        })),
        customerId,
        tenantId,
      });
    },

    // Intelligence
    async getRecommendations(itemId, limit = 5) {
      const res = await post<{ recommendations: Recommendation[] }>('/v1/pos/recommend', {
        itemId,
        tenantId,
        limit,
      });
      return res.recommendations || [];
    },

    async getQuickOrder(customerId, limit = 10) {
      const res = await post<{ items: QuickOrderItem[] }>('/v1/pos/quick-order', {
        customerId,
        tenantId,
        limit,
      });
      return res.items || [];
    },

    async getMessages() {
      const res = await get<{ messages: CashierMessage[] }>(
        `/v1/pos/messages/${deviceId}?tenantId=${tenantId}`,
      );
      return res.messages || [];
    },

    async ackMessage(messageId) {
      await post(`/v1/pos/messages/${messageId}/ack`, { deviceId });
    },

    async getAnalytics(minutes = 60) {
      return get<PosAnalytics>(`/v1/pos/analytics?tenantId=${tenantId}&minutes=${minutes}`);
    },

    // Queue
    flush,

    getQueueSize() {
      return _queue.length;
    },

    startAutoFlush() {
      if (_flushTimer) return;
      _flushTimer = setInterval(() => {
        flush().catch(() => {});
      }, flushIntervalMs);
    },

    stopAutoFlush() {
      if (_flushTimer) {
        clearInterval(_flushTimer);
        _flushTimer = null;
      }
    },

    destroy() {
      sdk.stopAutoFlush();
      _queue = [];
    },
  };

  // Auto-start flush if offline queue enabled
  if (offlineQueue) {
    sdk.startAutoFlush();
  }

  return sdk;
}
