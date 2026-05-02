from django.shortcuts import render
from django.http import JsonResponse
from .models import Product, Order
from .services import get_event_log

def dashboard_view(request):
    """Main dashboard view"""
    products = Product.objects.all()
    orders = Order.objects.all()[:10]  # Last 10 orders
    events = get_event_log()

    context = {
        "products_count": products.count(),
        "products": products[:5],
        "orders_count": orders.count(),
        "orders": orders,
        "events_count": len(events),
        "recent_events": events[-10:],
    }

    return render(request, "dashboard.html", context)

def event_log_view(request):
    """JSON API for event log"""
    events = get_event_log()
    return JsonResponse({"events": events, "count": len(events)})
