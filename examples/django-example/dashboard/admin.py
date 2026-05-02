from django.contrib import admin
from .models import Product, Order
from .services import track_event

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "price", "quantity", "category"]
    list_filter = ["category", "updated_at"]
    search_fields = ["name", "sku"]
    readonly_fields = ["created_at", "updated_at"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Track inventory update
        track_event(
            event_name="inventory_updated",
            entity_type="product",
            entity_id=obj.sku,
            metadata={
                "name": obj.name,
                "quantity": obj.quantity,
                "price": float(obj.price),
                "updated_by": request.user.username if request.user else "admin",
            },
        )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_id", "total", "status", "items_count", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_id"]
    readonly_fields = ["order_id", "created_at", "updated_at"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # Track order update
        track_event(
            event_name="order_updated",
            entity_type="order",
            entity_id=obj.order_id,
            metadata={
                "status": obj.status,
                "total": float(obj.total),
                "items": obj.items_count,
            },
        )
