using System.Text.Json.Serialization;

namespace Aros.POS.SDK;

// ---------------------------------------------------------------------------
// Connexus event envelope
// ---------------------------------------------------------------------------

/// <summary>
/// Wire format for a single POS event sent to the Connexus ingest endpoint.
/// </summary>
public sealed class ConnexusEvent
{
    [JsonPropertyName("vendor")]
    public string Vendor { get; set; } = string.Empty;

    [JsonPropertyName("eventType")]
    public string EventType { get; set; } = string.Empty;

    [JsonPropertyName("data")]
    public Dictionary<string, object?> Data { get; set; } = new();

    [JsonPropertyName("deviceId")]
    public string DeviceId { get; set; } = string.Empty;

    [JsonPropertyName("tenantId")]
    public string TenantId { get; set; } = string.Empty;

    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = DateTimeOffset.UtcNow.ToString("o");
}

// ---------------------------------------------------------------------------
// Event data models — passed into fire-and-forget methods
// ---------------------------------------------------------------------------

/// <summary>
/// Item scanned or added to the basket.
/// </summary>
public sealed class ItemData
{
    [JsonPropertyName("barcode")]
    public string Barcode { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("price")]
    public decimal Price { get; set; }

    [JsonPropertyName("quantity")]
    public int Quantity { get; set; } = 1;

    [JsonPropertyName("department")]
    public string? Department { get; set; }

    [JsonPropertyName("category")]
    public string? Category { get; set; }
}

/// <summary>
/// Completed transaction / tender event.
/// </summary>
public sealed class TransactionData
{
    [JsonPropertyName("transactionId")]
    public string TransactionId { get; set; } = string.Empty;

    [JsonPropertyName("total")]
    public decimal Total { get; set; }

    [JsonPropertyName("paymentMethod")]
    public string PaymentMethod { get; set; } = "cash";

    [JsonPropertyName("itemCount")]
    public int ItemCount { get; set; }

    [JsonPropertyName("cashierId")]
    public string? CashierId { get; set; }

    [JsonPropertyName("items")]
    public List<ItemData>? Items { get; set; }
}

/// <summary>
/// Voided item or transaction.
/// </summary>
public sealed class VoidData
{
    [JsonPropertyName("transactionId")]
    public string? TransactionId { get; set; }

    [JsonPropertyName("barcode")]
    public string? Barcode { get; set; }

    [JsonPropertyName("reason")]
    public string? Reason { get; set; }

    [JsonPropertyName("amount")]
    public decimal Amount { get; set; }

    [JsonPropertyName("cashierId")]
    public string? CashierId { get; set; }
}

/// <summary>
/// Discount applied to item or transaction.
/// </summary>
public sealed class DiscountData
{
    [JsonPropertyName("barcode")]
    public string? Barcode { get; set; }

    [JsonPropertyName("discountType")]
    public string DiscountType { get; set; } = "percentage";

    [JsonPropertyName("value")]
    public decimal Value { get; set; }

    [JsonPropertyName("reason")]
    public string? Reason { get; set; }

    [JsonPropertyName("promoCode")]
    public string? PromoCode { get; set; }
}

/// <summary>
/// Manual price override on an item.
/// </summary>
public sealed class PriceOverrideData
{
    [JsonPropertyName("barcode")]
    public string Barcode { get; set; } = string.Empty;

    [JsonPropertyName("originalPrice")]
    public decimal OriginalPrice { get; set; }

    [JsonPropertyName("newPrice")]
    public decimal NewPrice { get; set; }

    [JsonPropertyName("reason")]
    public string? Reason { get; set; }

    [JsonPropertyName("cashierId")]
    public string? CashierId { get; set; }

    [JsonPropertyName("managerApproval")]
    public bool ManagerApproval { get; set; }
}

/// <summary>
/// Customer identification event (loyalty card, phone lookup).
/// </summary>
public sealed class CustomerData
{
    [JsonPropertyName("customerId")]
    public string CustomerId { get; set; } = string.Empty;

    [JsonPropertyName("loyaltyNumber")]
    public string? LoyaltyNumber { get; set; }

    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("tier")]
    public string? Tier { get; set; }

    [JsonPropertyName("totalVisits")]
    public int? TotalVisits { get; set; }
}

/// <summary>
/// Fuel dispenser event (c-store / gas station).
/// </summary>
public sealed class FuelData
{
    [JsonPropertyName("pumpNumber")]
    public int PumpNumber { get; set; }

    [JsonPropertyName("fuelType")]
    public string FuelType { get; set; } = "regular";

    [JsonPropertyName("gallons")]
    public decimal Gallons { get; set; }

    [JsonPropertyName("pricePerGallon")]
    public decimal PricePerGallon { get; set; }

    [JsonPropertyName("total")]
    public decimal Total { get; set; }

    [JsonPropertyName("prepay")]
    public bool Prepay { get; set; }
}

// ---------------------------------------------------------------------------
// Intelligence response models — returned from async query methods
// ---------------------------------------------------------------------------

/// <summary>
/// A single product recommendation returned by the AROS engine.
/// </summary>
public sealed class Recommendation
{
    [JsonPropertyName("itemId")]
    public string ItemId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("reason")]
    public string? Reason { get; set; }

    [JsonPropertyName("confidence")]
    public double Confidence { get; set; }

    [JsonPropertyName("price")]
    public decimal? Price { get; set; }

    [JsonPropertyName("category")]
    public string? Category { get; set; }

    [JsonPropertyName("imageUrl")]
    public string? ImageUrl { get; set; }
}

/// <summary>
/// A message pushed to a cashier's register by the AROS intelligence layer.
/// </summary>
public sealed class CashierMessage
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("type")]
    public string Type { get; set; } = "info";

    [JsonPropertyName("title")]
    public string? Title { get; set; }

    [JsonPropertyName("body")]
    public string Body { get; set; } = string.Empty;

    [JsonPropertyName("priority")]
    public string Priority { get; set; } = "normal";

    [JsonPropertyName("createdAt")]
    public string? CreatedAt { get; set; }

    [JsonPropertyName("expiresAt")]
    public string? ExpiresAt { get; set; }
}

/// <summary>
/// A pre-built quick-order item for one-tap ordering.
/// </summary>
public sealed class QuickOrderItem
{
    [JsonPropertyName("itemId")]
    public string ItemId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("price")]
    public decimal Price { get; set; }

    [JsonPropertyName("category")]
    public string? Category { get; set; }

    [JsonPropertyName("imageUrl")]
    public string? ImageUrl { get; set; }

    [JsonPropertyName("popularity")]
    public double Popularity { get; set; }
}

/// <summary>
/// Analytics snapshot for a device or tenant.
/// </summary>
public sealed class PosAnalytics
{
    [JsonPropertyName("tenantId")]
    public string TenantId { get; set; } = string.Empty;

    [JsonPropertyName("deviceId")]
    public string? DeviceId { get; set; }

    [JsonPropertyName("period")]
    public string Period { get; set; } = "today";

    [JsonPropertyName("totalTransactions")]
    public int TotalTransactions { get; set; }

    [JsonPropertyName("totalRevenue")]
    public decimal TotalRevenue { get; set; }

    [JsonPropertyName("averageBasketSize")]
    public decimal AverageBasketSize { get; set; }

    [JsonPropertyName("topItems")]
    public List<TopItem>? TopItems { get; set; }

    [JsonPropertyName("hourlyBreakdown")]
    public List<HourlyBucket>? HourlyBreakdown { get; set; }
}

/// <summary>
/// A top-selling item in the analytics response.
/// </summary>
public sealed class TopItem
{
    [JsonPropertyName("itemId")]
    public string ItemId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("unitsSold")]
    public int UnitsSold { get; set; }

    [JsonPropertyName("revenue")]
    public decimal Revenue { get; set; }
}

/// <summary>
/// Hourly revenue bucket in the analytics response.
/// </summary>
public sealed class HourlyBucket
{
    [JsonPropertyName("hour")]
    public int Hour { get; set; }

    [JsonPropertyName("transactions")]
    public int Transactions { get; set; }

    [JsonPropertyName("revenue")]
    public decimal Revenue { get; set; }
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

/// <summary>
/// Payload sent when registering a device with Connexus.
/// </summary>
public sealed class DeviceRegistration
{
    [JsonPropertyName("vendor")]
    public string Vendor { get; set; } = string.Empty;

    [JsonPropertyName("deviceId")]
    public string DeviceId { get; set; } = string.Empty;

    [JsonPropertyName("tenantId")]
    public string TenantId { get; set; } = string.Empty;

    [JsonPropertyName("capabilities")]
    public List<string>? Capabilities { get; set; }

    [JsonPropertyName("sdkVersion")]
    public string SdkVersion { get; set; } = "dotnet-1.0.0";
}

/// <summary>
/// Registration response from the Connexus API.
/// </summary>
public sealed class RegistrationResult
{
    [JsonPropertyName("success")]
    public bool Success { get; set; }

    [JsonPropertyName("sessionId")]
    public string? SessionId { get; set; }

    [JsonPropertyName("message")]
    public string? Message { get; set; }
}
