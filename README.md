# AROS Developer Portal

Developer portal and SDKs for integrating any POS system with the AROS AI platform.

## SDKs

| Platform | Directory | Package | Status |
|----------|-----------|---------|--------|
| JavaScript/TypeScript | `sdks/javascript/` | `@aros/pos-sdk` | npm |
| Python | `sdks/python/` | `aros-pos-sdk` | PyPI |
| C# / .NET | `sdks/dotnet/` | `Aros.POS.SDK` | NuGet |
| Swift (iOS/macOS) | `sdks/swift/` | `ArosPOS` | SwiftPM |
| Kotlin (Android) | `sdks/kotlin/` | `com.aros:pos-sdk` | Maven |
| REST API | `sdks/rest/` | OpenAPI 3.1 spec | Any language |

## Portal

Developer documentation site built with React + Vite.

```bash
cd portal
npm install
npm run dev    # http://localhost:3200
```

## Quick Start

### JavaScript
```bash
npm install @aros/pos-sdk
```

```typescript
import { createArosPOS } from "@aros/pos-sdk";

const pos = createArosPOS({
  endpoint: "http://your-server:5497",
  tenantId: "store-42",
  vendor: "verifone-commander",
  deviceId: "REG-001",
});

pos.itemScanned({ barcode: "012345", price: 14.99, description: "Fireball" });
const recs = await pos.getRecommendations("SKU-001");
```

### Python
```bash
pip install aros-pos-sdk
```

```python
from aros_pos import create_aros_pos

pos = create_aros_pos(
    endpoint="http://your-server:5497",
    tenant_id="store-42",
    vendor="verifone-commander",
    device_id="REG-001",
)

pos.item_scanned(barcode="012345", price=14.99, description="Fireball")
recs = pos.get_recommendations("SKU-001")
```

## Supported POS Systems

Verifone Commander, Verifone Ruby, NCR Aloha, NCR Counterpoint, NCR Voyix, Gilbarco Passport, Gilbarco FlexPay, Wayne Fusion, Oracle Simphony, Clover, Square, Toast, Lightspeed, Shopify POS, RapidRMS MobilePOS, and any custom system via the generic adapter.

## Architecture

```
POS System → @aros/pos-sdk → Shre Router → CortexDB → AROS AI Agents
                                  ↓
                          Recommendations ← Association Engine
                          Messages       ← Manager/AROS Agents
                          Quick Orders   ← Customer Memory
```

## License

MIT
