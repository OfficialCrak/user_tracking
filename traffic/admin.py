from django.contrib import admin
from .models import TrafficStat


@admin.register(TrafficStat)
class TrafficStatAdmin(admin.ModelAdmin):
    list_display = ('id', 'ip_address', 'user_agent', 'created_at', 'url', 'event', 'session_id')
    search_fields = ('ip_address', 'user_agent', 'url', 'session_id')
    list_filter = ('created_at', 'event')
