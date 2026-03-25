# @aros/pos-sdk

Connect **any POS system** to the AROS AI platform for real-time intelligence, upsell recommendations, loss prevention, and cashier messaging.

**Zero dependencies.** Works in Node.js, React Native, Electron, or browser.

## Install

```bash
npm install @aros/pos-sdk
```

## Quick Start

```typescript
import { createArosPOS } from "@aros/pos-sdk";

const pos = createArosPOS({
  endpoint: "https://your-shre-instance.com",
  tenantId: "store-42",
  vendor: "verifone-commander",
  deviceId: "REG-001",
  apiKey: "your-api-key",
});

// Register your device (call once on startup)
await pos.register({ model: "Commander 2.0", firmware: "4.1.2" });

// Send events as they happen (fire-and-forget, auto-queues offline)
pos.itemScanned({ barcode: "012345678901", description: "Corona 12pk", price: 16.99 });
pos.transactionComplete({ total: 42.50, paymentType: "credit", itemCount: 3 });

// Get AI-powered recommendations
const recs = await pos.getRecommendations("item-123");
// → [{ target_item: "lime-6pk", target_description: "Lime 6pk", confidence: 0.82, ... }]

// Get cashier messages/alerts
const messages = await pos.getMessages();
// → [{ title: "Restock cooler #3", priority: 1, ... }]
```

## Supported POS Systems

| Vendor | ID | Notes |
|--------|----|-------|
| RapidRMS MobilePOS | `mobilepos` | Native integration via Redux middleware |
| Verifone Commander | `verifone-commander` | C-store, fuel controller |
| Verifone Ruby2/RubyCi | `verifone-ruby` | Convenience, grocery |
| NCR Aloha | `ncr-aloha` | Restaurant |
| NCR Counterpoint | `ncr-counterpoint` | Retail |
| NCR Voyix | `ncr-voyix` | Grocery, general retail |
| Gilbarco Passport | `gilbarco-passport` | Fuel + c-store |
| Gilbarco FlexPay | `gilbarco-flexpay` | Fuel dispenser |
| Wayne Fusion | `wayne-fusion` | Fuel |
| Oracle Simphony | `oracle-simphony` | Hospitality |
| Clover | `clover` | SMB retail/restaurant |
| Square | `square` | SMB |
| Toast | `toast` | Restaurant |
| Lightspeed | `lightspeed` | Retail/restaurant |
| Shopify POS | `shopify-pos` | Retail |
| Custom | `custom-<name>` | Any other system |

## Events API

All event methods are **fire-and-forget**. They queue locally and flush every 30 seconds (configurable). Events never block your POS flow.

### Item Events

```typescript
// Item scanned / added to cart
pos.itemScanned({
  barcode: "012345678901",
  itemId: "SKU-001",
  description: "Fireball 750ml",
  price: 14.99,
  quantity: 1,
  department: "Liquor",
  itemType: "merchandise",
});

// Quantity changed
pos.quantityChanged({
  itemId: "SKU-001",
  description: "Fireball 750ml",
  price: 14.99,
  direction: "PLUS",
  newQuantity: 3,
});

// Fuel dispensed
pos.fuelDispensed({
  pumpNumber: "4",
  fuelGrade: "Regular 87",
  gallons: 12.5,
  total: 43.75,
});
```

### Transaction Events

```typescript
// Sale completed
pos.transactionComplete({
  transactionId: "INV-2024-1234",
  total: 42.50,
  subtotal: 39.25,
  tax: 3.25,
  itemCount: 3,
  paymentType: "credit",
  cashierName: "John",
  // Include items to auto-learn co-purchase patterns
  items: [
    { itemId: "SKU-001", description: "Corona 12pk", price: 16.99 },
    { itemId: "SKU-002", description: "Lime 6pk", price: 3.99 },
    { itemId: "SKU-003", description: "Doritos", price: 4.29 },
  ],
});
```

### Loss Prevention Events

```typescript
// Void a line item
pos.voidLine({
  itemId: "SKU-001",
  reason: "customer_changed_mind",
  amount: 14.99,
  cashierName: "John",
});

// Void entire transaction
pos.voidTransaction({
  transactionId: "INV-2024-1234",
  reason: "register_error",
  cashierName: "John",
});

// Return / refund
pos.returnItem({
  transactionId: "INV-2024-1200",
  itemId: "SKU-001",
  amount: 14.99,
  reason: "defective",
});

// Discount applied
pos.discountApplied({
  itemId: "SKU-001",
  discountType: "employee",
  amount: 2.00,
  scope: "item",
});

// Price override
pos.priceOverride({
  itemId: "SKU-001",
  originalPrice: 14.99,
  newPrice: 12.99,
  reason: "damaged_packaging",
  cashierName: "John",
});

// No-sale / drawer opened without transaction
pos.noSale({ reason: "make_change", cashierName: "John" });
```

### Customer Events

```typescript
// Loyalty card scanned
pos.customerIdentified({
  loyaltyNumber: "LYL-789456",
  customerName: "Jane Doe",
  loyaltyTier: "gold",
});
```

## Intelligence API

### Upsell / Cross-sell Recommendations

Called after an item is scanned. Returns items frequently purchased together.

```typescript
const recs = await pos.getRecommendations("SKU-001", 3);
// [
//   { target_item: "SKU-002", target_description: "Lime 6pk",
//     target_price: 3.99, co_purchase_count: 47, confidence: 0.82 },
//   { target_item: "SKU-003", target_description: "Modelo 12pk",
//     target_price: 15.99, co_purchase_count: 31, confidence: 0.65 },
// ]
```

### Customer Quick Order

Returns the customer's most frequently purchased items for one-tap ring-up.

```typescript
const items = await pos.getQuickOrder("LYL-789456", 5);
// [
//   { item_id: "SKU-010", description: "Marlboro Gold", price: 9.50, purchase_count: 23 },
//   { item_id: "SKU-020", description: "Monster Energy 2pk", price: 5.99, purchase_count: 18 },
// ]
```

### Cashier Messages

Retrieve todo items, alerts, and shift notes pushed by managers or AROS agents.

```typescript
const messages = await pos.getMessages();
for (const msg of messages) {
  console.log(`[${msg.type}] ${msg.title}: ${msg.body}`);
  // Show on POS screen...
  await pos.ackMessage(msg.id); // Mark as done
}
```

### Real-time Analytics

```typescript
const stats = await pos.getAnalytics(60); // Last 60 minutes
console.log(`${stats.transactions} transactions, $${stats.totalRevenue} revenue`);
console.log(`Alerts: ${stats.alerts.voids} voids, ${stats.alerts.noSales} no-sales`);
```

## Configuration

```typescript
const pos = createArosPOS({
  // Required
  endpoint: "https://your-shre-instance.com",
  tenantId: "store-42",
  vendor: "verifone-commander",
  deviceId: "REG-001",

  // Optional
  apiKey: "your-api-key",           // Required for cloud, optional for local
  timeoutMs: 10_000,                // HTTP request timeout (default: 10s)
  offlineQueue: true,               // Queue events when offline (default: true)
  maxQueueSize: 500,                // Max queued events (default: 500)
  flushIntervalMs: 30_000,          // Auto-flush interval (default: 30s)

  // React Native: pass your own fetch
  fetchFn: fetch,

  // Callbacks
  onError: (err, event) => {
    console.warn("AROS event failed:", err.message, event.eventType);
  },
  onFlush: (count, success) => {
    console.log(`Flushed ${count} events: ${success ? "OK" : "FAILED"}`);
  },
});
```

## Vendor-Specific Examples

### Verifone Commander (C-store / Fuel)

```typescript
// In your Verifone Commander plugin or extension:
import { createArosPOS } from "@aros/pos-sdk";

const pos = createArosPOS({
  endpoint: "http://backoffice-ip:5497",
  tenantId: "site-123",
  vendor: "verifone-commander",
  deviceId: `VFI-${getTerminalId()}`,
});

// Hook into Commander's event system
commander.on("itemSold", (item) => {
  pos.itemScanned({
    barcode: item.UPC,
    description: item.Description,
    price: item.UnitPrice,
    quantity: item.Quantity,
    department: item.Department,
  });
});

commander.on("transactionComplete", (txn) => {
  pos.transactionComplete({
    transactionId: txn.TransactionID,
    total: txn.GrandTotal,
    tax: txn.TaxAmount,
    paymentType: txn.TenderType,
    itemCount: txn.LineItemCount,
    items: txn.Items?.map(i => ({
      itemId: i.ItemID,
      description: i.Description,
      price: i.UnitPrice,
    })),
  });
});

// Fuel dispensing
commander.on("dispenserComplete", (pump) => {
  pos.fuelDispensed({
    pumpNumber: pump.DispenserID,
    fuelGrade: pump.GradeDescription,
    gallons: pump.Volume,
    total: pump.SaleAmount,
  });
});
```

### NCR Counterpoint (Retail)

```typescript
import { createArosPOS } from "@aros/pos-sdk";

const pos = createArosPOS({
  endpoint: "http://localhost:5497",
  tenantId: "store-ncr-01",
  vendor: "ncr-counterpoint",
  deviceId: `NCR-LANE-${getLaneId()}`,
});

// NCR event hooks
ncr.onLineItemAdded((item) => {
  pos.itemScanned({
    barcode: item.PLU,
    itemId: item.productId,
    description: item.itemName,
    price: item.amount,
    quantity: item.qty,
    department: item.deptCode,
  });
});

// Real-time upsell on every scan
ncr.onLineItemAdded(async (item) => {
  const recs = await pos.getRecommendations(item.productId);
  if (recs.length > 0) {
    ncr.showOperatorPrompt(`Suggest: ${recs[0].target_description} ($${recs[0].target_price})`);
  }
});
```

### Gilbarco Passport (Fuel + C-Store)

```typescript
import { createArosPOS } from "@aros/pos-sdk";

const pos = createArosPOS({
  endpoint: "http://backoffice:5497",
  tenantId: "fuel-mart-7",
  vendor: "gilbarco-passport",
  deviceId: `GBR-${getPassportId()}`,
});

// Passport event hooks
passport.on("EndOfTransaction", (txn) => {
  pos.transactionComplete({
    transactionId: txn.InvoiceNo,
    total: txn.GrandTotal,
    paymentType: txn.PaymentMethod,
    cashierName: txn.CashierID,
  });
});

passport.on("DispenserComplete", (pump) => {
  pos.fuelDispensed({
    pumpNumber: pump.DispenserID,
    fuelGrade: pump.ProductName,
    gallons: pump.Quantity,
    total: pump.SaleAmount,
  });
});
```

## Architecture

```
Your POS System
    │
    ▼
@aros/pos-sdk (this package)
    │ HTTP / Connexus protocol
    ▼
Shre Router (:5497)
    ├── /v1/connexus/ingest      → normalizes events → CortexDB
    ├── /v1/pos/recommend        → upsell/cross-sell engine
    ├── /v1/pos/quick-order      → customer purchase history
    ├── /v1/pos/messages/:did    → cashier todo/alerts
    └── /v1/pos/analytics        → real-time analytics
    │
    ▼
AROS AI Agents (block-based execution)
    ├── Ana    → inventory intelligence, reorder drafts
    ├── Victor → fraud detection, void patterns
    ├── Sammy  → P&L, revenue anomalies
    ├── Larry  → labor optimization
    └── Rita   → reputation management
```

## License

MIT
