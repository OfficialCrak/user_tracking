from django.contrib import admin
from .models import TrafficStat


@admin.register(TrafficStat)
class TrafficStatAdmin(admin.ModelAdmin):
    list_display = ('id', 'ip_address', 'user_name', 'user_agent', 'created_at', 'url', 'event', 'session_id')
    search_fields = ('user__first_name', 'user__last_name', 'ip_address', 'user__email', 'url')

    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else "-"

    user_name.short_description = 'Имя пользователя'

    list_filter = ('created_at', 'event')
