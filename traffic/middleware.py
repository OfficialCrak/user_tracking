from .models import TrafficStat


class TrafficTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        TrafficStat.objects.create(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            url=request.path,
            session_id=request.session.session_key,
        )

        return response
