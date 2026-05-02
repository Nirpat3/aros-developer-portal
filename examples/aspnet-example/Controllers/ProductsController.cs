using Microsoft.AspNetCore.Mvc;

namespace ShreSdkExample.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ProductsController : ControllerBase
    {
        private readonly ShreSDK _shre;
        private readonly IEventQueueService _eventQueue;

        private static readonly List<ProductDto> Products = new()
        {
            new() { Id = "1", Name = "Laptop", Price = 999, Stock = 10, Category = "electronics" },
            new() { Id = "2", Name = "Mouse", Price = 29, Stock = 50, Category = "accessories" },
            new() { Id = "3", Name = "Keyboard", Price = 79, Stock = 30, Category = "accessories" },
            new() { Id = "4", Name = "Monitor", Price = 299, Stock = 15, Category = "electronics" },
        };

        public ProductsController(ShreSDK shre, IEventQueueService eventQueue)
        {
            _shre = shre;
            _eventQueue = eventQueue;
        }

        [HttpGet]
        public async Task<IActionResult> GetProducts()
        {
            await _eventQueue.AddEvent(new EventDto
            {
                EventName = "product_list_view",
                EntityType = "page",
                EntityId = "products",
                Metadata = new Dictionary<string, object> { { "count", Products.Count } },
            });

            return Ok(new { products = Products, count = Products.Count });
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> GetProduct(string id)
        {
            var product = Products.FirstOrDefault(p => p.Id == id);
            if (product == null)
                return NotFound(new { error = "not found" });

            await _eventQueue.AddEvent(new EventDto
            {
                EventName = "product_view",
                EntityType = "product",
                EntityId = id,
                Metadata = new Dictionary<string, object>
                {
                    { "name", product.Name },
                    { "price", product.Price },
                    { "category", product.Category },
                },
            });

            return Ok(product);
        }
    }

    public class ProductDto
    {
        public string? Id { get; set; }
        public string? Name { get; set; }
        public decimal Price { get; set; }
        public int Stock { get; set; }
        public string? Category { get; set; }
    }
}
