from django.conf import settings
from django.db import models
from django.utils import timezone


class TrafficStat(models.Model):
    ip_address = models.GenericIPAddressField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='traffic_stats'
    )
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    url = models.CharField(max_length=255, blank=True, null=True)
    event = models.CharField(max_length=255, blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'Трафик с {self.id} в {self.created_at}'

    class Meta:
        verbose_name = 'Трафик сети'
        verbose_name_plural = 'Статистика трафика'
