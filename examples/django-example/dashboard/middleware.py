from django.conf import settings
from .services import track_event

class ShreEventTrackingMiddleware:
    """Track HTTP requests via Shre SDK"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip tracking for static/media files
        if request.path.startswith(("/static/", "/media/", "/health", "/readyz")):
            return self.get_response(request)

        # Track request
        track_event(
            event_name="http_request",
            entity_type="request",
            entity_id=f"{request.method}_{request.path}",
            metadata={
                "method": request.method,
                "path": request.path,
                "user": str(request.user) if request.user else "anonymous",
            },
        )

        response = self.get_response(request)
        return response
