from rest_framework import generics
from .models import TrafficStat
from .serializers import TrafficStatSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.utils import timezone
from django.db.models.functions import TruncDay, TruncMonth, TruncHour
from datetime import datetime
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class DailyTrafficStats(generics.ListAPIView):
    serializer_class = TrafficStatSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='date',
                in_=openapi.IN_QUERY,
                description="Дата в формате YYYY-MM-DD. Если не указана, статистика будет по текущему дню.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=False
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        date_str = request.query_params.get('date', None)

        if date_str:
            try:
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "Неверный формат даты. Используйте YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            selected_date = timezone.now().date()

        start_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))

        queryset = TrafficStat.objects.filter(created_at__range=(start_of_day, end_of_day))
        queryset = queryset.annotate(hour=TruncHour('created_at')).values('hour').annotate(count=Count('id')).order_by('hour')

        if not queryset.exists():
            return Response(
                {"error": f"Нет данных по дате {selected_date}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        unique_users_count = queryset.values('session_id').distinct().count()

        data = {
            'traffic': [{'hour': stat['hour'].hour, 'count': stat['count']} for stat in queryset],
            'unique_users': unique_users_count,
        }

        return Response(data, status=status.HTTP_200_OK)


class WeeklyTrafficStats(generics.ListAPIView):
    serializer_class = TrafficStatSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='week',
                in_=openapi.IN_QUERY,
                description="Неделя в формате YYYY-WW. Если не указан, статистика по текущей неделе.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=False
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        week_str = request.query_params.get('week', None)

        if week_str:
            try:
                year, week = map(int, week_str.split('-'))
                selected_date = datetime.strptime(f'{year}-W{week}-1', "%Y-W%W-%w").date()
                start_of_week = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            except ValueError:
                return TrafficStat.objects.none()
        else:
            now = timezone.now()
            start_of_week = now - timezone.timedelta(days=now.weekday())

        end_of_week = start_of_week + timezone.timedelta(days=6, hours=23, minutes=59, seconds=59)

        queryset = TrafficStat.objects.filter(created_at__range=(start_of_week, end_of_week))
        queryset = queryset.annotate(day=TruncDay('created_at')).values('day').annotate(count=Count('id')).order_by('day')

        if not queryset.exists():
            return Response(
                {"error": "Неправильный формат даты или нету записи с такой датой"},
                status=status.HTTP_400_BAD_REQUEST
            )

        unique_users_count = queryset.values('session_id').distinct().count()

        data = {
            'traffic': [{'day': stat['day'].strftime('%A'), 'count': stat['count']} for stat in queryset],
            'unique_users': unique_users_count,
        }

        return Response(data, status=status.HTTP_200_OK)


class MonthlyTrafficStats(generics.ListAPIView):
    serializer_class = TrafficStatSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='month',
                in_=openapi.IN_QUERY,
                description="Месяц в формате YYYY-MM. Если не указан, статистика по текущему месяцу.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=False
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        month_str = request.query_params.get('month', None)

        if month_str:
            try:
                selected_month = datetime.strptime(month_str, '%Y-%m')
            except ValueError:
                return Response(
                    {"error": "Неверный формат месяца. Используйте YYYY-MM"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            selected_month = timezone.now()

        start_of_month = timezone.make_aware(datetime(selected_month.year, selected_month.month, 1))
        next_month = selected_month.replace(month=(selected_month.month % 12) + 1)
        end_of_month = timezone.make_aware(datetime(next_month.year, next_month.month, 1) - timezone.timedelta(days=1))

        queryset = TrafficStat.objects.filter(created_at__range=(start_of_month, end_of_month))
        queryset = queryset.annotate(day=TruncDay('created_at')).values('day').annotate(count=Count('id')).order_by('day')

        if not queryset.exists():
            return Response(
                {"error": f"Нет данных для месяца {month_str or selected_month.strftime('%Y-%m')}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        unique_users_count = queryset.values('session_id').distinct().count()

        data = {
            'traffic': [{'day': stat['day'].strftime('%d'), 'count': stat['count']} for stat in queryset],
            'unique_users': unique_users_count,
        }

        return Response(data, status=status.HTTP_200_OK)


class YearlyTrafficStats(generics.ListAPIView):
    serializer_class = TrafficStatSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='year',
                in_=openapi.IN_QUERY,
                description="Год в формате YYYY. Если не указан, статистика по текущему году.",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                required=False
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        year_str = request.query_params.get('year', None)

        if year_str:
            try:
                selected_year = datetime.strptime(year_str, '%Y')
            except ValueError:
                return Response(
                    {"error": "Неверный формат года. Используйте YYYY"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            selected_year = timezone.now()

        start_of_year = timezone.make_aware(datetime(selected_year.year, 1, 1))
        end_of_year = timezone.make_aware(datetime(selected_year.year, 12, 31, 23, 59, 59))

        queryset = TrafficStat.objects.filter(created_at__range=(start_of_year, end_of_year))
        queryset = queryset.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')

        if not queryset.exists():
            return Response(
                {"error": f"Нет данных для года {year_str or selected_year.year}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        unique_users_count = queryset.values('session_id').distinct().count()

        data = {
            'traffic': [{'month': stat['month'].strftime('%B'), 'count': stat['count']} for stat in queryset],
            'unique_users': unique_users_count,
        }

        return Response(data, status=status.HTTP_200_OK)

