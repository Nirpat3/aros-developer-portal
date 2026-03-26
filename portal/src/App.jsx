import React, { useState } from 'react';

const SDKS = [
  { icon: '🟨', name: 'JavaScript / TypeScript', desc: 'Node.js, React, React Native, Electron, Browser', install: 'npm install @aros/pos-sdk', lang: 'javascript' },
  { icon: '🐍', name: 'Python', desc: 'Linux servers, data pipelines, Django, Flask', install: 'pip install aros-pos-sdk', lang: 'python' },
  { icon: '🟦', name: 'C# / .NET', desc: 'Windows POS, WPF, WinForms, .NET 6+', install: 'dotnet add package Aros.POS.SDK', lang: 'dotnet' },
  { icon: '🍎', name: 'Swift (iOS/macOS)', desc: 'iOS POS apps, iPad registers, macOS', install: '.package(url: "...ArosPOS", from: "1.0.0")', lang: 'swift' },
  { icon: '🤖', name: 'Kotlin (Android)', desc: 'Android POS devices, tablets, kiosks', install: 'implementation("com.aros:pos-sdk:1.0.0")', lang: 'kotlin' },
  { icon: '🌐', name: 'REST API', desc: 'Any language — cURL, Go, Rust, PHP, Ruby', install: 'curl -X POST /v1/connexus/ingest', lang: 'rest' },
];

const VENDORS = [
  { name: 'Verifone Commander', id: 'verifone-commander', type: 'C-Store / Fuel' },
  { name: 'Verifone Ruby', id: 'verifone-ruby', type: 'Convenience' },
  { name: 'NCR Aloha', id: 'ncr-aloha', type: 'Restaurant' },
  { name: 'NCR Counterpoint', id: 'ncr-counterpoint', type: 'Retail' },
  { name: 'NCR Voyix', id: 'ncr-voyix', type: 'Grocery' },
  { name: 'Gilbarco Passport', id: 'gilbarco-passport', type: 'Fuel + C-Store' },
  { name: 'Gilbarco FlexPay', id: 'gilbarco-flexpay', type: 'Fuel Dispenser' },
  { name: 'Wayne Fusion', id: 'wayne-fusion', type: 'Fuel' },
  { name: 'Oracle Simphony', id: 'oracle-simphony', type: 'Hospitality' },
  { name: 'Clover', id: 'clover', type: 'SMB Retail' },
  { name: 'Square', id: 'square', type: 'SMB' },
  { name: 'Toast', id: 'toast', type: 'Restaurant' },
  { name: 'Lightspeed', id: 'lightspeed', type: 'Retail / Restaurant' },
  { name: 'Shopify POS', id: 'shopify-pos', type: 'Retail' },
  { name: 'RapidRMS MobilePOS', id: 'mobilepos', type: 'C-Store / Retail' },
  { name: 'Custom', id: 'custom-*', type: 'Any System' },
];

const EVENTS = [
  { method: 'itemScanned()', event: 'ItemSale', desc: 'Item scanned / added to cart', category: 'Sales' },
  { method: 'quantityChanged()', event: 'qty_change', desc: 'Quantity +/- on cart item', category: 'Sales' },
  { method: 'transactionComplete()', event: 'TransactionComplete', desc: 'Sale completed', category: 'Sales' },
  { method: 'fuelDispensed()', event: 'FuelDispense', desc: 'Fuel pump completed', category: 'Sales' },
  { method: 'voidLine()', event: 'VoidLine', desc: 'Single item voided', category: 'Loss Prevention' },
  { method: 'voidTransaction()', event: 'VoidTransaction', desc: 'Entire transaction voided', category: 'Loss Prevention' },
  { method: 'returnItem()', event: 'Return', desc: 'Item returned / refunded', category: 'Loss Prevention' },
  { method: 'discountApplied()', event: 'Discount', desc: 'Discount applied (item or transaction)', category: 'Loss Prevention' },
  { method: 'priceOverride()', event: 'PriceOverride', desc: 'Manual price change', category: 'Loss Prevention' },
  { method: 'noSale()', event: 'NoSale', desc: 'Drawer opened without sale', category: 'Loss Prevention' },
  { method: 'customerIdentified()', event: 'LoyaltySwipe', desc: 'Customer loyalty card scanned', category: 'Customer' },
];

const CODE_EXAMPLES = {
  javascript: `import { createArosPOS } from "@aros/pos-sdk";

const pos = createArosPOS({
  endpoint: "http://your-server:5497",
  tenantId: "store-42",
  vendor: "verifone-commander",
  deviceId: "REG-001",
  apiKey: "your-api-key",
});

// Register device (call once on startup)
await pos.register({ model: "Commander 2.0" });

// Send events (fire-and-forget, queues offline)
pos.itemScanned({
  barcode: "012345678901",
  description: "Fireball 750ml",
  price: 14.99,
  department: "Liquor",
});

pos.transactionComplete({
  total: 42.50,
  paymentType: "credit",
  items: [
    { itemId: "SKU-001", description: "Fireball", price: 14.99 },
    { itemId: "SKU-002", description: "Doritos", price: 4.29 },
  ],
});

// Get AI recommendations
const recs = await pos.getRecommendations("SKU-001");
console.log(recs[0].target_description); // "Lime 6pk"

// Get cashier messages
const msgs = await pos.getMessages();
msgs.forEach(m => console.log(m.title));`,

  python: `from aros_pos import create_aros_pos

pos = create_aros_pos(
    endpoint="http://your-server:5497",
    tenant_id="store-42",
    vendor="verifone-commander",
    device_id="REG-001",
    api_key="your-api-key",
)

# Register device
pos.register(model="Commander 2.0")

# Send events (fire-and-forget, queues offline)
pos.item_scanned(
    barcode="012345678901",
    description="Fireball 750ml",
    price=14.99,
    department="Liquor",
)

pos.transaction_complete(
    total=42.50,
    payment_type="credit",
    items=[
        {"item_id": "SKU-001", "description": "Fireball", "price": 14.99},
        {"item_id": "SKU-002", "description": "Doritos", "price": 4.29},
    ],
)

# Get AI recommendations
recs = pos.get_recommendations("SKU-001")
print(recs[0]["target_description"])  # "Lime 6pk"

# Get cashier messages
for msg in pos.get_messages():
    print(msg["title"])`,

  dotnet: `using Aros.POS.SDK;

var pos = ArosPOS.Create(new ArosPOSConfig {
    Endpoint = "http://your-server:5497",
    TenantId = "store-42",
    Vendor = "verifone-commander",
    DeviceId = "REG-001",
    ApiKey = "your-api-key",
});

// Register device
await pos.RegisterAsync(model: "Commander 2.0");

// Send events (fire-and-forget, queues offline)
pos.ItemScanned(new ItemData {
    Barcode = "012345678901",
    Description = "Fireball 750ml",
    Price = 14.99m,
    Department = "Liquor",
});

pos.TransactionComplete(new TransactionData {
    Total = 42.50m,
    PaymentType = "credit",
    ItemCount = 3,
});

// Get AI recommendations
var recs = await pos.GetRecommendationsAsync("SKU-001");
Console.WriteLine(recs[0].TargetDescription); // "Lime 6pk"

// Get cashier messages
var msgs = await pos.GetMessagesAsync();
foreach (var m in msgs) Console.WriteLine(m.Title);`,

  swift: `import ArosPOS

let pos = ArosPOS(config: .init(
    endpoint: "http://your-server:5497",
    tenantId: "store-42",
    vendor: .verifoneCommander,
    deviceId: "REG-001",
    apiKey: "your-api-key"
))

// Register device
try await pos.register(model: "Commander 2.0")

// Send events (fire-and-forget, queues offline)
pos.itemScanned(ItemData(
    barcode: "012345678901",
    description: "Fireball 750ml",
    price: 14.99,
    department: "Liquor"
))

pos.transactionComplete(TransactionData(
    total: 42.50,
    paymentType: "credit",
    itemCount: 3
))

// Get AI recommendations
let recs = try await pos.getRecommendations(itemId: "SKU-001")
print(recs.first?.targetDescription ?? "") // "Lime 6pk"

// Get cashier messages
let msgs = try await pos.getMessages()
msgs.forEach { print($0.title) }`,

  kotlin: `import com.aros.pos.ArosPOS
import com.aros.pos.ArosPOSConfig
import com.aros.pos.PosVendor

val pos = ArosPOS(ArosPOSConfig(
    endpoint = "http://your-server:5497",
    tenantId = "store-42",
    vendor = PosVendor.VERIFONE_COMMANDER,
    deviceId = "REG-001",
    apiKey = "your-api-key"
))

// Register device
pos.register(model = "Commander 2.0")

// Send events (fire-and-forget, queues offline)
pos.itemScanned(ItemData(
    barcode = "012345678901",
    description = "Fireball 750ml",
    price = 14.99,
    department = "Liquor"
))

pos.transactionComplete(TransactionData(
    total = 42.50,
    paymentType = "credit",
    itemCount = 3
))

// Get AI recommendations
val recs = pos.getRecommendations("SKU-001")
println(recs.first().targetDescription) // "Lime 6pk"

// Get cashier messages
pos.getMessages().forEach { println(it.title) }`,

  rest: `# Register device
curl -X POST http://your-server:5497/v1/connexus/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "deviceId": "REG-001",
    "tenantId": "store-42",
    "vendor": "verifone-commander",
    "model": "Commander 2.0"
  }'

# Send item scan event
curl -X POST http://your-server:5497/v1/connexus/ingest \\
  -H "Content-Type: application/json" \\
  -d '{
    "vendor": "verifone-commander",
    "eventType": "ItemSale",
    "deviceId": "REG-001",
    "tenantId": "store-42",
    "data": {
      "barcode": "012345678901",
      "description": "Fireball 750ml",
      "price": 14.99,
      "department": "Liquor"
    }
  }'

# Get recommendations
curl -X POST http://your-server:5497/v1/pos/recommend \\
  -H "Content-Type: application/json" \\
  -d '{"itemId": "SKU-001", "tenantId": "store-42"}'

# Get cashier messages
curl http://your-server:5497/v1/pos/messages/REG-001?tenantId=store-42`,
};

function Header() {
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);
  return (
    <header className="header">
      <div className="container">
        <div className="logo">AROS <span>Developer Portal</span></div>
        <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
          <span /><span /><span />
        </button>
        <nav className={menuOpen ? 'open' : ''}>
          <a href="#sdks" onClick={closeMenu}>SDKs</a>
          <a href="#quickstart" onClick={closeMenu}>Quick Start</a>
          <a href="#events" onClick={closeMenu}>Events</a>
          <a href="#intelligence" onClick={closeMenu}>Intelligence</a>
          <a href="#vendors" onClick={closeMenu}>POS Systems</a>
          <a href="#architecture" onClick={closeMenu}>Architecture</a>
          <a href="https://github.com/Nirpat3/aros-developer-portal" target="_blank" rel="noopener">GitHub</a>
        </nav>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="hero">
      <div className="container">
        <h1>Connect any <span>POS system</span> to AI</h1>
        <p>
          AROS POS SDKs bring real-time intelligence, upsell recommendations,
          loss prevention, and cashier messaging to every register.
          5 lines of code. Zero dependencies.
        </p>
        <div className="hero-actions">
          <a href="#quickstart" className="btn btn-primary">Get Started</a>
          <a href="#sdks" className="btn btn-outline">View SDKs</a>
          <a href="/openapi.yaml" className="btn btn-outline">API Reference</a>
        </div>
      </div>
    </section>
  );
}

function Features() {
  return (
    <section className="section">
      <div className="container">
        <div className="features">
          <div className="feature">
            <div className="badge badge-green">Real-time</div>
            <h3>Upsell & Cross-sell</h3>
            <p>AI-powered product recommendations based on co-purchase patterns. "72% of Corona buyers also grab limes."</p>
          </div>
          <div className="feature">
            <div className="badge badge-blue">Intelligence</div>
            <h3>Customer Quick Order</h3>
            <p>One-tap repeat orders from purchase history. Regular customers served in seconds, not minutes.</p>
          </div>
          <div className="feature">
            <div className="badge badge-yellow">Prevention</div>
            <h3>Loss Prevention</h3>
            <p>Track voids, returns, no-sales, price overrides. Victor AI agent detects patterns in real-time.</p>
          </div>
          <div className="feature">
            <div className="badge badge-green">Messaging</div>
            <h3>Cashier Todo & Alerts</h3>
            <p>Push messages to registers: restock alerts, shift notes, compliance reminders, low inventory warnings.</p>
          </div>
          <div className="feature">
            <div className="badge badge-blue">Offline-first</div>
            <h3>Queue & Auto-flush</h3>
            <p>Events queue locally when offline and auto-flush on reconnect. Never blocks POS flow. Never loses data.</p>
          </div>
          <div className="feature">
            <div className="badge badge-yellow">Standard</div>
            <h3>Connexus Protocol</h3>
            <p>Industry-standard event format. Works with Verifone, NCR, Gilbarco, or any POS system.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function SDKSection() {
  return (
    <section id="sdks" className="section">
      <div className="container">
        <h2>SDKs</h2>
        <p className="subtitle">Choose your platform. Same API everywhere.</p>
        <div className="sdk-grid">
          {SDKS.map(sdk => (
            <div key={sdk.lang} className="sdk-card">
              <div className="icon">{sdk.icon}</div>
              <h3>{sdk.name}</h3>
              <p>{sdk.desc}</p>
              <div className="install">{sdk.install}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function QuickStart() {
  const [lang, setLang] = useState('javascript');
  return (
    <section id="quickstart" className="section">
      <div className="container">
        <h2>Quick Start</h2>
        <p className="subtitle">Full integration in under 10 lines of code.</p>
        <div className="tabs">
          {SDKS.map(sdk => (
            <button key={sdk.lang} className={`tab ${lang === sdk.lang ? 'active' : ''}`} onClick={() => setLang(sdk.lang)}>
              {sdk.icon} {sdk.name.split(' /')[0].split(' (')[0]}
            </button>
          ))}
        </div>
        <pre>{CODE_EXAMPLES[lang]}</pre>
      </div>
    </section>
  );
}

function EventsSection() {
  return (
    <section id="events" className="section">
      <div className="container">
        <h2>Events</h2>
        <p className="subtitle">Every POS action becomes an AI training signal.</p>
        <table>
          <thead>
            <tr><th>SDK Method</th><th>Event Type</th><th>Description</th><th>Category</th></tr>
          </thead>
          <tbody>
            {EVENTS.map(e => (
              <tr key={e.method}>
                <td><code>{e.method}</code></td>
                <td><code>{e.event}</code></td>
                <td>{e.desc}</td>
                <td>{e.category}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function IntelligenceSection() {
  return (
    <section id="intelligence" className="section">
      <div className="container">
        <h2>AI Intelligence</h2>
        <p className="subtitle">The platform gets smarter with every scan.</p>
        <div className="features">
          <div className="feature">
            <h3>POST /v1/pos/recommend</h3>
            <p>Pass an itemId after scan. Returns co-purchase recommendations ranked by confidence. Learns from every basket.</p>
            <pre style={{marginTop: 12, fontSize: 12}}>{`{
  "itemId": "SKU-001",
  "recommendations": [
    { "target_description": "Lime 6pk",
      "confidence": 0.82,
      "co_purchase_count": 47 }
  ]
}`}</pre>
          </div>
          <div className="feature">
            <h3>POST /v1/pos/quick-order</h3>
            <p>Pass a customerId (loyalty card). Returns their most purchased items. One-tap ring-up for regulars.</p>
            <pre style={{marginTop: 12, fontSize: 12}}>{`{
  "customerId": "LYL-789",
  "items": [
    { "description": "Marlboro Gold",
      "price": 9.50,
      "purchase_count": 23 }
  ]
}`}</pre>
          </div>
          <div className="feature">
            <h3>GET /v1/pos/messages/:deviceId</h3>
            <p>Retrieve cashier todo items, alerts, shift notes. Push from MIB007 dashboard or AROS agents.</p>
            <pre style={{marginTop: 12, fontSize: 12}}>{`{
  "messages": [
    { "type": "todo",
      "title": "Restock cooler #3",
      "priority": 1,
      "source": "ana" }
  ]
}`}</pre>
          </div>
        </div>
      </div>
    </section>
  );
}

function VendorSection() {
  return (
    <section id="vendors" className="section">
      <div className="container">
        <h2>Supported POS Systems</h2>
        <p className="subtitle">16 vendors supported out of the box. Custom integrations via generic adapter.</p>
        <div className="vendor-grid">
          {VENDORS.map(v => (
            <div key={v.id} className="vendor-card">
              <div className="name">{v.name}</div>
              <div className="id">{v.id}</div>
              <div style={{fontSize: 11, color: 'var(--text-dim)', marginTop: 4}}>{v.type}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Architecture() {
  return (
    <section id="architecture" className="section">
      <div className="container">
        <h2>Architecture</h2>
        <p className="subtitle">How data flows from your register to AI intelligence and back.</p>
        <div className="arch-diagram">{`Your POS System (any vendor)
    |
    v
@aros/pos-sdk (JS, Python, C#, Swift, Kotlin, or REST)
    |  Connexus protocol (HTTP/JSON)
    v
+------------------------------------------+
|  Shre Router (:5497)                     |
|                                          |
|  /v1/connexus/ingest   -> Normalizer     |
|  /v1/pos/recommend     -> Association AI |
|  /v1/pos/quick-order   -> Customer Memory|
|  /v1/pos/messages      -> Message Queue  |
|  /v1/pos/analytics     -> Real-time Agg  |
+------------------------------------------+
    |                           |
    v                           v
CortexDB (PostgreSQL +      AROS Block System
 Qdrant + Redis)             (wave executor)
    |                           |
    v                           v
+----------+  +----------+  +----------+  +----------+  +----------+
| Ana      |  | Victor   |  | Sammy    |  | Larry    |  | Rita     |
| Inventory|  | Fraud    |  | Revenue  |  | Labor    |  | Reviews  |
| P7       |  | P9       |  | P6       |  | P5       |  | P4       |
+----------+  +----------+  +----------+  +----------+  +----------+
    |                           |
    v                           v
MIB007 Dashboard          Shre Chat (conversational)
(tasks, drafts,           "What's selling right now?"
 approvals)               "Any fraud alerts today?"`}
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <p>AROS Developer Portal — Built by Nirlab Inc. Powered by Shre AI.</p>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <>
      <Header />
      <Hero />
      <Features />
      <SDKSection />
      <QuickStart />
      <EventsSection />
      <IntelligenceSection />
      <VendorSection />
      <Architecture />
      <Footer />
    </>
  );
}
