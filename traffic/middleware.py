from .models import TrafficStat


class TrafficTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/static/'):
            return self.get_response(request)

        if request.path.startswith('/admin/jsi18n/'):
            return self.get_response(request)

        if request.path.startswith('/admin/'):
            if request.path.startswith('/admin/js/') or request.path.startswith('/admin/img/') or request.path.startswith('/admin/css/'):
                return self.get_response(request)

        if not request.session.session_key:
            request.session.create()

        session_id = request.session.session_key
        response = self.get_response(request)

        TrafficStat.objects.create(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            url=request.path,
            session_id=session_id,
        )

        return response
