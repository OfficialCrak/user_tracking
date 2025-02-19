from .models import TrafficStat
from django.contrib.auth.models import AnonymousUser


class TrafficTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/static/') or \
                request.path.startswith('/admin/jsi18n/') or \
                request.path.startswith('/admin/js/') or \
                request.path.startswith('/admin/img/') or \
                request.path.startswith('/admin/css/') or \
                request.path == '/favicon.ico':

            return self.get_response(request)

        if not request.session.session_key:
            request.session.create()

        session_id = request.session.session_key
        response = self.get_response(request)

        user = request.user if not isinstance(request.user, AnonymousUser) else None

        TrafficStat.objects.create(
            ip_address=request.META.get('REMOTE_ADDR'),
            user=user,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            url=request.path,
            session_id=session_id,
        )

        return response
