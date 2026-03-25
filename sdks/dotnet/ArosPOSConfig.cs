namespace Aros.POS.SDK;

/// <summary>
/// Configuration for the AROS POS SDK client.
/// </summary>
public sealed class ArosPOSConfig
{
    /// <summary>
    /// Base URL of the AROS API (e.g. "http://server:5497").
    /// </summary>
    public string Endpoint { get; set; } = "http://localhost:5497";

    /// <summary>
    /// Tenant identifier for this store location.
    /// </summary>
    public string TenantId { get; set; } = string.Empty;

    /// <summary>
    /// POS vendor identifier. Must be one of the supported vendors.
    /// </summary>
    public string Vendor { get; set; } = "generic";

    /// <summary>
    /// Unique device/register identifier.
    /// </summary>
    public string DeviceId { get; set; } = string.Empty;

    /// <summary>
    /// Optional API key for authenticated endpoints.
    /// </summary>
    public string? ApiKey { get; set; }

    /// <summary>
    /// Maximum number of events to buffer before forcing a flush.
    /// </summary>
    public int BatchSize { get; set; } = 50;

    /// <summary>
    /// Interval in milliseconds between automatic queue flushes.
    /// </summary>
    public int FlushIntervalMs { get; set; } = 5000;

    /// <summary>
    /// HTTP request timeout in seconds.
    /// </summary>
    public int TimeoutSeconds { get; set; } = 10;

    /// <summary>
    /// Maximum number of events to hold in the offline queue.
    /// Events beyond this limit are silently dropped.
    /// </summary>
    public int MaxQueueSize { get; set; } = 10_000;

    /// <summary>
    /// Supported POS vendor identifiers.
    /// </summary>
    public static readonly IReadOnlyList<string> SupportedVendors = new[]
    {
        "mobilepos",
        "verifone-commander",
        "verifone-ruby",
        "ncr-aloha",
        "ncr-counterpoint",
        "ncr-voyix",
        "gilbarco-passport",
        "gilbarco-flexpay",
        "wayne-fusion",
        "oracle-simphony",
        "clover",
        "square",
        "toast",
        "lightspeed",
        "shopify-pos",
        "generic"
    };

    /// <summary>
    /// Validates the configuration and throws if invalid.
    /// </summary>
    public void Validate()
    {
        if (string.IsNullOrWhiteSpace(Endpoint))
            throw new ArgumentException("Endpoint is required.", nameof(Endpoint));

        if (string.IsNullOrWhiteSpace(TenantId))
            throw new ArgumentException("TenantId is required.", nameof(TenantId));

        if (string.IsNullOrWhiteSpace(DeviceId))
            throw new ArgumentException("DeviceId is required.", nameof(DeviceId));

        if (!SupportedVendors.Contains(Vendor))
            throw new ArgumentException(
                $"Unsupported vendor '{Vendor}'. Must be one of: {string.Join(", ", SupportedVendors)}",
                nameof(Vendor));

        if (BatchSize < 1)
            throw new ArgumentException("BatchSize must be at least 1.", nameof(BatchSize));

        if (FlushIntervalMs < 500)
            throw new ArgumentException("FlushIntervalMs must be at least 500.", nameof(FlushIntervalMs));
    }
}
