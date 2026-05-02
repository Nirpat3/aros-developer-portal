# Shre SDK ASP.NET Core Example

Working ASP.NET Core REST API demonstrating Shre SDK integration with dependency injection.

## Features

- **Dependency Injection**: ShreSDK + EventQueueService registered
- **REST API**: Product and Order endpoints
- **Event Queuing**: In-memory queue with manual flush
- **Swagger UI**: Interactive API documentation
- **Event Tracking**: All API calls auto-tracked

## Running

```bash
dotnet restore
dotnet build
dotnet run
# Starts on http://localhost:5000
# Swagger: http://localhost:5000/swagger
```

## API Endpoints

### Products
- `GET /api/products` — List all products
- `GET /api/products/{id}` — Get product details

### Orders
- `POST /api/orders` — Create new order
- `GET /api/orders/{orderId}` — Get order status
- `GET /api/orders/queue/status` — View queued events
- `POST /api/orders/queue/flush` — Manually flush events

### Health
- `GET /health` — Service health
- `GET /readyz` — Ready check

## How Events Flow

1. **API Call** → Product view, order creation
2. **Event Created** → Added to in-memory queue
3. **Manual Flush** → POST /api/orders/queue/flush
4. **Auto-Flush** → Could be scheduled background task

## Integration Example

```csharp
public class OrdersController : ControllerBase
{
    private readonly IEventQueueService _eventQueue;

    public OrdersController(IEventQueueService eventQueue)
    {
        _eventQueue = eventQueue;
    }

    [HttpPost]
    public async Task<IActionResult> CreateOrder(CreateOrderDto dto)
    {
        // Create order...

        // Track event
        await _eventQueue.AddEvent(new EventDto
        {
            EventName = "order_created",
            EntityType = "order",
            EntityId = orderId,
            Metadata = new Dictionary<string, object>
            {
                { "total", dto.Total }
            },
        });

        return Created($"/api/orders/{orderId}", order);
    }
}
```

## Production Checklist

- [ ] Change tenant_id to your workspace ID
- [ ] Implement background event flushing
- [ ] Add database persistence for orders
- [ ] Configure proper error handling
- [ ] Set up health monitoring
- [ ] Deploy to cloud infrastructure
