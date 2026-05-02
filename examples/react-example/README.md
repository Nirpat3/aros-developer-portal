# Shre SDK React Example

Working React application demonstrating Shre SDK event tracking integration.

## Features

- **Product Catalog**: Browse and view 6 sample products
- **Shopping Cart**: Add items and checkout
- **Event Tracking**: Real-time event log showing:
  - `pageview` — initial page load
  - `product_view` — user views a product
  - `cart_add` — item added to cart
  - `purchase` — checkout completed

## Running Locally

```bash
npm install
npm run dev
# Opens http://localhost:5173
```

## How It Works

1. **SDK Initialization**: On app load, creates ShreSDK instance for tenant `dev-tenant-001`
2. **Event Tracking**: Each user action (view/cart/checkout) sends event via `sendEventsBatch()`
3. **Event Log**: UI displays all events with timestamp and status (sent/error)

## Integration Points

The app sends events to:
```
POST https://apiauth.shre.ai/v1/events/batch
```

With headers:
```
x-shre-tenant: dev-tenant-001
x-shre-app: web
```

## Production Notes

- Change `tenantId` to your workspace ID
- Use `https://apiauth.shre.ai` (default) for production
- Handle API errors gracefully (already implemented)
- Implement retry logic for failed events (see cart implementation)
