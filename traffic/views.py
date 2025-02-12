from rest_framework import generics
from .models import TrafficStat
from .serializers import TrafficStatSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.utils import timezone
from django.db.models.functions import TruncDay, TruncMonth, TruncYear


class DailyTrafficStats(generics.ListAPIView):
    serializer_class = TrafficStatSerializer

    def get_queryset(self):
        now = timezone.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        stats = TrafficStat.objects.filter(created_at__gte=start_of_day)
        stats = stats.annotate(hour=TruncDay('created_at')).values('hour').annotate(count=Count('id')).order_by('hour')
        return stats

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unique_users_count = queryset.values('session_id').distinct().count()

        data = {
            'traffic': [{'hour': stat['hour'].hour, 'count': stat['count']} for stat in queryset],
            'unique_users': unique_users_count,
        }
        return Response(data, status=status.HTTP_200_OK)


class WeeklyTrafficStats(generics.ListAPIView):
    serializer_class = TrafficStatSerializer

    def get_queryset(self):
        now = timezone.now()
        start_of_week = now - timezone.timedelta(days=now.weekday())
        stats = TrafficStat.objects.filter(created_at__gte=start_of_week)
        stats = stats.annotate(day=TruncDay('created_at')).values('day').annotate(count=Count('id')).order_by('day')
        return stats

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unique_users_count = queryset.values('session_id').distinct().count()

        data = {
            'traffic': [{'day': stat['day'].strftime('%A'), 'count': stat['count']} for stat in queryset],
            'unique_users': unique_users_count,
        }
        return Response(data, status=status.HTTP_200_OK)


class MonthlyTrafficStats(generics.ListAPIView):
    serializer_class = TrafficStatSerializer

    def get_queryset(self):
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stats = TrafficStat.objects.filter(created_at__gte=start_of_month)
        stats = stats.annotate(day=TruncDay('created_at')).values('day').annotate(count=Count('id')).order_by('day')
        return stats

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unique_users_count = queryset.values('session_id').distinct().count()

        data = {
            'traffic': [{'day': stat['day'].strftime('%d'), 'count': stat['count']} for stat in queryset],
            'unique_users': unique_users_count,
        }
        return Response(data, status=status.HTTP_200_OK)


class YearlyTrafficStats(generics.ListAPIView):
    serializer_class = TrafficStatSerializer

    def get_queryset(self):
        now = timezone.now()
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        stats = TrafficStat.objects.filter(created_at__gte=start_of_year)
        stats = stats.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
        return stats

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unique_users_count = queryset.values('session_id').distinct().count()

        data = {
            'traffic': [{'month': stat['month'].strftime('%B'), 'count': stat['count']} for stat in queryset],
            'unique_users': unique_users_count,
        }
        return Response(data, status=status.HTTP_200_OK)
