# Shre SDK Django Example

Working Django application with admin integration demonstrating automatic event tracking.

## Features

- **Django Admin**: Full admin interface for Products & Orders
- **Auto-Tracking**: Admin saves auto-trigger Shre events
- **Middleware**: Request tracking on all endpoints
- **Dashboard**: Real-time view of products, orders, events
- **Event Log**: Live display of tracked events

## Running

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then:
- **Admin**: http://localhost:8000/admin/ (use credentials created above)
- **Dashboard**: http://localhost:8000/

## How It Works

1. **Admin saves Product**: `ProductAdmin.save_model()` calls `track_event()`
2. **Event queued**: Event sent to Shre via SDK
3. **Dashboard updates**: Event appears in real-time log
4. **Middleware**: Every HTTP request also tracked

## Integration Points

### Admin Integration
```python
class ProductAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        track_event("inventory_updated", "product", obj.sku, {
            "quantity": obj.quantity,
            "price": float(obj.price),
        })
```

### Middleware Integration
```python
class ShreEventTrackingMiddleware:
    def __call__(self, request):
        track_event("http_request", "request", f"{request.method}_{request.path}")
        return self.get_response(request)
```

## Production Notes

- Change `SECRET_KEY` in settings.py
- Use PostgreSQL instead of SQLite
- Deploy event batch flushing background task
- Monitor event queue depth
