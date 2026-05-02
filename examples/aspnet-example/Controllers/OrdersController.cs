using Microsoft.AspNetCore.Mvc;

namespace ShreSdkExample.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class OrdersController : ControllerBase
    {
        private readonly ShreSDK _shre;
        private readonly IEventQueueService _eventQueue;

        public OrdersController(ShreSDK shre, IEventQueueService eventQueue)
        {
            _shre = shre;
            _eventQueue = eventQueue;
        }

        [HttpPost]
        public async Task<IActionResult> CreateOrder([FromBody] CreateOrderDto dto)
        {
            var orderId = Guid.NewGuid().ToString();

            await _eventQueue.AddEvent(new EventDto
            {
                EventName = "order_created",
                EntityType = "order",
                EntityId = orderId,
                Metadata = new Dictionary<string, object>
                {
                    { "items", dto.Items?.Count ?? 0 },
                    { "total", dto.Total },
                    { "customer", dto.Customer ?? "" },
                },
            });

            return Created($"/api/orders/{orderId}", new
            {
                orderId,
                status = "created",
                items = dto.Items,
                total = dto.Total,
            });
        }

        [HttpGet("{orderId}")]
        public async Task<IActionResult> GetOrder(string orderId)
        {
            await _eventQueue.AddEvent(new EventDto
            {
                EventName = "order_view",
                EntityType = "order",
                EntityId = orderId,
            });

            return Ok(new
            {
                orderId,
                status = "pending",
                createdAt = DateTime.UtcNow,
            });
        }

        [HttpGet("queue/status")]
        public async Task<IActionResult> GetQueueStatus()
        {
            var events = await _eventQueue.GetQueuedEvents();
            return Ok(new { queued = events.Count, events });
        }

        [HttpPost("queue/flush")]
        public async Task<IActionResult> FlushQueue()
        {
            var result = await _eventQueue.FlushAsync(_shre);
            return Ok(result);
        }
    }

    public class CreateOrderDto
    {
        public List<string>? Items { get; set; }
        public decimal Total { get; set; }
        public string? Customer { get; set; }
    }
}
