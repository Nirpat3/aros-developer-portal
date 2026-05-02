var builder = WebApplication.CreateBuilder(args);

// Add services
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// Register Shre SDK
builder.Services.AddSingleton(sp =>
    new ShreSDK(
        tenantId: "dev-tenant-001",
        appPlatform: "dotnet"
    )
);

// Register event queue service
builder.Services.AddSingleton<IEventQueueService, EventQueueService>();

// Add CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin().AllowAnyMethod().AllowAnyHeader();
    });
});

var app = builder.Build();

app.UseCors();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseRouting();

app.MapControllers();

// Health endpoints
app.MapGet("/health", () => new { status = "ok", service = "shre-aspnet-example" })
    .WithName("Health")
    .WithOpenApi();

app.MapGet("/readyz", () => new { ready = true })
    .WithName("Readiness")
    .WithOpenApi();

app.Run("http://0.0.0.0:5000");

public class ShreSDK
{
    private readonly string _tenantId;
    private readonly string _appPlatform;
    private readonly string _baseUrl = "https://apiauth.shre.ai";
    private readonly HttpClient _client = new();

    public ShreSDK(string tenantId, string appPlatform = "dotnet")
    {
        _tenantId = tenantId;
        _appPlatform = appPlatform;
    }

    public async Task<Dictionary<string, object>> SendEventsBatchAsync(List<EventDto> events)
    {
        var url = $"{_baseUrl}/v1/events/batch";
        var headers = new Dictionary<string, string>
        {
            { "x-shre-tenant", _tenantId },
            { "x-shre-app", _appPlatform },
        };

        var content = new StringContent(
            System.Text.Json.JsonSerializer.Serialize(new { events }),
            System.Text.Encoding.UTF8,
            "application/json"
        );

        var request = new HttpRequestMessage(HttpMethod.Post, url) { Content = content };
        foreach (var header in headers)
        {
            request.Headers.Add(header.Key, header.Value);
        }

        var response = await _client.SendAsync(request);
        var responseText = await response.Content.ReadAsStringAsync();

        if (!response.IsSuccessStatusCode)
            throw new Exception($"HTTP {response.StatusCode}: {responseText}");

        return System.Text.Json.JsonSerializer.Deserialize<Dictionary<string, object>>(responseText) ?? new();
    }
}

public class EventDto
{
    public string EventId { get; set; } = Guid.NewGuid().ToString();
    public string EventName { get; set; } = string.Empty;
    public string EntityType { get; set; } = string.Empty;
    public string EntityId { get; set; } = string.Empty;
    public Dictionary<string, object>? Metadata { get; set; }
    public string Timestamp { get; set; } = DateTime.UtcNow.ToString("O");
}

public interface IEventQueueService
{
    Task AddEvent(EventDto @event);
    Task<List<EventDto>> GetQueuedEvents();
    Task<Dictionary<string, object>> FlushAsync(ShreSDK sdk);
}

public class EventQueueService : IEventQueueService
{
    private readonly List<EventDto> _queue = new();
    private readonly object _lock = new();

    public Task AddEvent(EventDto @event)
    {
        lock (_lock)
        {
            _queue.Add(@event);
        }
        return Task.CompletedTask;
    }

    public Task<List<EventDto>> GetQueuedEvents()
    {
        lock (_lock)
        {
            return Task.FromResult(new List<EventDto>(_queue));
        }
    }

    public async Task<Dictionary<string, object>> FlushAsync(ShreSDK sdk)
    {
        List<EventDto> eventsToSend;
        lock (_lock)
        {
            if (_queue.Count == 0)
                return new Dictionary<string, object> { { "flushed", 0 } };

            eventsToSend = new List<EventDto>(_queue);
            _queue.Clear();
        }

        var response = await sdk.SendEventsBatchAsync(eventsToSend);
        response["flushed"] = eventsToSend.Count;
        return response;
    }
}
