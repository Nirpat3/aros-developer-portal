using System.Collections.Concurrent;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using System.Timers;
using Timer = System.Timers.Timer;

namespace Aros.POS.SDK;

/// <summary>
/// AROS POS SDK client — offline-capable event ingestion and real-time
/// intelligence for Windows POS systems.
///
/// Thread-safe. All event methods are fire-and-forget (enqueue to an offline
/// buffer). Intelligence methods are async and hit the network directly.
/// Call <see cref="Dispose"/> (or use <c>using</c>) to flush remaining events
/// and release resources.
/// </summary>
public sealed class ArosPOS : IDisposable
{
    // -------------------------------------------------------------------
    // Static factory
    // -------------------------------------------------------------------

    /// <summary>
    /// Create and register a new AROS POS client.
    /// </summary>
    public static ArosPOS Create(ArosPOSConfig config)
    {
        config.Validate();
        return new ArosPOS(config);
    }

    // -------------------------------------------------------------------
    // Fields
    // -------------------------------------------------------------------

    private readonly ArosPOSConfig _config;
    private readonly HttpClient _http;
    private readonly ConcurrentQueue<ConnexusEvent> _queue = new();
    private readonly Timer _flushTimer;
    private readonly JsonSerializerOptions _json;
    private volatile int _queueSize;
    private volatile bool _disposed;

    // -------------------------------------------------------------------
    // Constructor (private — use Create)
    // -------------------------------------------------------------------

    private ArosPOS(ArosPOSConfig config)
    {
        _config = config;

        _json = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
        };

        _http = new HttpClient
        {
            BaseAddress = new Uri(config.Endpoint.TrimEnd('/')),
            Timeout = TimeSpan.FromSeconds(config.TimeoutSeconds)
        };
        _http.DefaultRequestHeaders.Accept.Add(
            new MediaTypeWithQualityHeaderValue("application/json"));

        if (!string.IsNullOrWhiteSpace(config.ApiKey))
            _http.DefaultRequestHeaders.Authorization =
                new AuthenticationHeaderValue("Bearer", config.ApiKey);

        _flushTimer = new Timer(config.FlushIntervalMs);
        _flushTimer.Elapsed += OnFlushTimer;
        _flushTimer.AutoReset = true;
        _flushTimer.Start();
    }

    // -------------------------------------------------------------------
    // Registration
    // -------------------------------------------------------------------

    /// <summary>
    /// Register this device with the Connexus gateway.
    /// Call once at POS startup.
    /// </summary>
    public async Task<RegistrationResult> RegisterAsync(
        List<string>? capabilities = null,
        CancellationToken ct = default)
    {
        ThrowIfDisposed();

        var payload = new DeviceRegistration
        {
            Vendor = _config.Vendor,
            DeviceId = _config.DeviceId,
            TenantId = _config.TenantId,
            Capabilities = capabilities
        };

        var response = await _http.PostAsJsonAsync(
            "/v1/connexus/register", payload, _json, ct).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        return await response.Content
            .ReadFromJsonAsync<RegistrationResult>(_json, ct).ConfigureAwait(false)
            ?? new RegistrationResult { Success = false, Message = "Empty response" };
    }

    // -------------------------------------------------------------------
    // Fire-and-forget event methods (enqueue to offline buffer)
    // -------------------------------------------------------------------

    /// <summary>Item scanned or added to the basket.</summary>
    public void ItemScanned(ItemData data) =>
        Enqueue("item_scanned", data);

    /// <summary>Transaction completed / tendered.</summary>
    public void TransactionCompleted(TransactionData data) =>
        Enqueue("transaction_completed", data);

    /// <summary>Item or transaction voided.</summary>
    public void VoidPerformed(VoidData data) =>
        Enqueue("void", data);

    /// <summary>Discount applied.</summary>
    public void DiscountApplied(DiscountData data) =>
        Enqueue("discount_applied", data);

    /// <summary>Manual price override.</summary>
    public void PriceOverride(PriceOverrideData data) =>
        Enqueue("price_override", data);

    /// <summary>Customer identified (loyalty, phone lookup).</summary>
    public void CustomerIdentified(CustomerData data) =>
        Enqueue("customer_identified", data);

    /// <summary>Fuel dispenser event.</summary>
    public void FuelDispensed(FuelData data) =>
        Enqueue("fuel_dispensed", data);

    /// <summary>
    /// Enqueue a custom event with an arbitrary event type and payload.
    /// </summary>
    public void TrackEvent(string eventType, Dictionary<string, object?> data) =>
        Enqueue(eventType, data);

    // -------------------------------------------------------------------
    // Intelligence methods (async, network-bound)
    // -------------------------------------------------------------------

    /// <summary>
    /// Get product recommendations for the current basket context.
    /// </summary>
    public async Task<List<Recommendation>> GetRecommendationsAsync(
        string? contextItemId = null,
        int limit = 5,
        CancellationToken ct = default)
    {
        ThrowIfDisposed();

        var payload = new Dictionary<string, object?>
        {
            ["tenantId"] = _config.TenantId,
            ["deviceId"] = _config.DeviceId,
            ["contextItemId"] = contextItemId,
            ["limit"] = limit
        };

        var response = await _http.PostAsJsonAsync(
            "/v1/pos/recommend", payload, _json, ct).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        return await response.Content
            .ReadFromJsonAsync<List<Recommendation>>(_json, ct).ConfigureAwait(false)
            ?? new List<Recommendation>();
    }

    /// <summary>
    /// Get quick-order items (popular / frequently purchased).
    /// </summary>
    public async Task<List<QuickOrderItem>> GetQuickOrderAsync(
        string? category = null,
        int limit = 10,
        CancellationToken ct = default)
    {
        ThrowIfDisposed();

        var payload = new Dictionary<string, object?>
        {
            ["tenantId"] = _config.TenantId,
            ["deviceId"] = _config.DeviceId,
            ["category"] = category,
            ["limit"] = limit
        };

        var response = await _http.PostAsJsonAsync(
            "/v1/pos/quick-order", payload, _json, ct).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        return await response.Content
            .ReadFromJsonAsync<List<QuickOrderItem>>(_json, ct).ConfigureAwait(false)
            ?? new List<QuickOrderItem>();
    }

    /// <summary>
    /// Retrieve pending messages for this register/device.
    /// </summary>
    public async Task<List<CashierMessage>> GetMessagesAsync(
        CancellationToken ct = default)
    {
        ThrowIfDisposed();

        var response = await _http.GetAsync(
            $"/v1/pos/messages/{Uri.EscapeDataString(_config.DeviceId)}", ct)
            .ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        return await response.Content
            .ReadFromJsonAsync<List<CashierMessage>>(_json, ct).ConfigureAwait(false)
            ?? new List<CashierMessage>();
    }

    /// <summary>
    /// Acknowledge (dismiss) a cashier message by its ID.
    /// </summary>
    public async Task AcknowledgeMessageAsync(
        string messageId,
        CancellationToken ct = default)
    {
        ThrowIfDisposed();

        var response = await _http.PostAsync(
            $"/v1/pos/messages/{Uri.EscapeDataString(messageId)}/ack",
            null, ct).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();
    }

    /// <summary>
    /// Retrieve analytics for this device/tenant.
    /// </summary>
    public async Task<PosAnalytics> GetAnalyticsAsync(
        string period = "today",
        CancellationToken ct = default)
    {
        ThrowIfDisposed();

        var url = $"/v1/pos/analytics?tenantId={Uri.EscapeDataString(_config.TenantId)}" +
                  $"&deviceId={Uri.EscapeDataString(_config.DeviceId)}" +
                  $"&period={Uri.EscapeDataString(period)}";

        var response = await _http.GetAsync(url, ct).ConfigureAwait(false);
        response.EnsureSuccessStatusCode();

        return await response.Content
            .ReadFromJsonAsync<PosAnalytics>(_json, ct).ConfigureAwait(false)
            ?? new PosAnalytics { TenantId = _config.TenantId };
    }

    // -------------------------------------------------------------------
    // Manual flush
    // -------------------------------------------------------------------

    /// <summary>
    /// Flush all queued events to the server immediately.
    /// Returns the number of events sent.
    /// </summary>
    public async Task<int> FlushAsync(CancellationToken ct = default)
    {
        ThrowIfDisposed();
        return await DrainQueueAsync(ct).ConfigureAwait(false);
    }

    // -------------------------------------------------------------------
    // Queue internals
    // -------------------------------------------------------------------

    private void Enqueue(string eventType, object data)
    {
        ThrowIfDisposed();

        if (_queueSize >= _config.MaxQueueSize)
            return; // silently drop — back-pressure

        var dict = data switch
        {
            Dictionary<string, object?> d => d,
            _ => JsonSerializer.Deserialize<Dictionary<string, object?>>(
                     JsonSerializer.Serialize(data, _json), _json)
                 ?? new Dictionary<string, object?>()
        };

        var evt = new ConnexusEvent
        {
            Vendor = _config.Vendor,
            EventType = eventType,
            Data = dict,
            DeviceId = _config.DeviceId,
            TenantId = _config.TenantId,
            Timestamp = DateTimeOffset.UtcNow.ToString("o")
        };

        _queue.Enqueue(evt);
        Interlocked.Increment(ref _queueSize);

        // If we hit batch size, flush eagerly on the thread-pool.
        if (_queueSize >= _config.BatchSize)
            _ = Task.Run(() => DrainQueueAsync(CancellationToken.None));
    }

    private void OnFlushTimer(object? sender, ElapsedEventArgs e)
    {
        if (_queue.IsEmpty) return;
        _ = Task.Run(() => DrainQueueAsync(CancellationToken.None));
    }

    private async Task<int> DrainQueueAsync(CancellationToken ct)
    {
        var batch = new List<ConnexusEvent>();
        while (_queue.TryDequeue(out var evt))
        {
            batch.Add(evt);
            Interlocked.Decrement(ref _queueSize);

            if (batch.Count >= _config.BatchSize)
                break;
        }

        if (batch.Count == 0)
            return 0;

        try
        {
            var payload = new { events = batch };
            var response = await _http.PostAsJsonAsync(
                "/v1/connexus/ingest", payload, _json, ct).ConfigureAwait(false);
            response.EnsureSuccessStatusCode();

            // Also feed the learning pipeline.
            _ = _http.PostAsJsonAsync(
                "/v1/connexus/ingest/learn", payload, _json, CancellationToken.None);

            return batch.Count;
        }
        catch
        {
            // Network failure — re-enqueue for retry on next flush.
            foreach (var evt in batch)
            {
                if (_queueSize < _config.MaxQueueSize)
                {
                    _queue.Enqueue(evt);
                    Interlocked.Increment(ref _queueSize);
                }
            }
            return 0;
        }
    }

    // -------------------------------------------------------------------
    // IDisposable
    // -------------------------------------------------------------------

    /// <summary>
    /// Flush remaining events and release all resources.
    /// </summary>
    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;

        _flushTimer.Stop();
        _flushTimer.Dispose();

        // Best-effort final flush (synchronous wait, bounded).
        try
        {
            DrainQueueAsync(CancellationToken.None)
                .ConfigureAwait(false)
                .GetAwaiter()
                .GetResult();
        }
        catch
        {
            // Swallow — we are shutting down.
        }

        _http.Dispose();
    }

    private void ThrowIfDisposed()
    {
        if (_disposed)
            throw new ObjectDisposedException(nameof(ArosPOS));
    }
}
