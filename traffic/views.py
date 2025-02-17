from collections import OrderedDict
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .models import TrafficStat
from tracking.models import Visitor
from .serializers import TrafficStatSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Max
from django.utils import timezone
from django.db.models.functions import TruncDay, TruncMonth, TruncHour
from datetime import datetime, timedelta, date
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()


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

        data = []
        for stat in queryset:
            unique_users_count = TrafficStat.objects.filter(
                created_at__hour=stat['hour'].hour,
                created_at__date=selected_date
            ).values('session_id').distinct().count()
            data.append({'hour': stat['hour'].hour, 'count': stat['count'], 'unique_users': unique_users_count})

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
                selected_date = date.fromisocalendar(year, week, 1)
                start_of_week = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()), timezone.get_current_timezone())

            except ValueError:
                return Response(
                    {"error": "Неверный формат недели. Используйте YYYY-WW"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            now = timezone.localtime(timezone.now())

            iso_year, iso_week, iso_weekday = now.isocalendar()

            start_of_week = now - timezone.timedelta(days=iso_weekday - 1)
            start_of_week = timezone.make_aware(datetime.combine(start_of_week.date(), datetime.min.time()), timezone.get_current_timezone())

        end_of_week = start_of_week + timezone.timedelta(days=6, hours=23, minutes=59, seconds=59)
        end_of_week = timezone.make_aware(datetime.combine(end_of_week.date(), datetime.max.time()), timezone.get_current_timezone())

        queryset = TrafficStat.objects.filter(created_at__range=(start_of_week, end_of_week))
        queryset = queryset.annotate(day=TruncDay('created_at')).values('day').annotate(count=Count('id')).order_by('day')

        if not queryset.exists():
            return Response(
                {"error": f"Нет данных для года {week_str}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = []
        for stat in queryset:
            unique_users_count = TrafficStat.objects.filter(
                created_at__date=stat['day']
            ).values('session_id').distinct().count()
            data.append({'day': stat['day'].strftime('%A'), 'count': stat['count'], 'unique_users': unique_users_count})
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

        data = []
        for stat in queryset:
            unique_users_count = TrafficStat.objects.filter(
                created_at__date=stat['day']
            ).values('session_id').distinct().count()
            data.append({'day': stat['day'].strftime('%d'), 'count': stat['count'], 'unique_users': unique_users_count})

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

        data = []
        for stat in queryset:
            unique_users_count = TrafficStat.objects.filter(
                created_at__month=stat['month'].month
            ).values('session_id').distinct().count()
            data.append(
                {'month': stat['month'].strftime('%B'), 'count': stat['count'], 'unique_users': unique_users_count})

        return Response(data, status=status.HTTP_200_OK)


class ActivityTrackingView(generics.CreateAPIView):
    queryset = TrafficStat.objects.all()
    serializer_class = TrafficStatSerializer

    def create(self, request, *args, **kwargs):
        last_activity_time = request.data.get('last_activity_time')

        if not last_activity_time:
            return Response(
                {"error": "Отсутствует время последней активности"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            last_activity_time = timezone.datetime.fromisoformat(last_activity_time)
            last_activity_time = timezone.make_aware(last_activity_time)
        except ValueError:
            return Response(
                {"error": "Неверный формат времени"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.session.session_key:
            request.session.create()

        session_id = request.session.session_key

        visitor, created = Visitor.objects.get_or_create(
            session_key=session_id,
            defaults={
                "ip_address": request.META.get('REMOTE_ADDR'),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "start_time": timezone.now(),
            }
        )

        TrafficStat.objects.create(
            session_id=session_id,
            event='activity',
            created_at=last_activity_time,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            url=request.path
        )

        return Response(
            {"message": "Активность выполнена успешна"},
            status=status.HTTP_201_CREATED
        )


class ActiveUsersView(APIView):
    def get(self, request, *args, **kwargs):
        thirty_minutes_ago = timezone.now() - timezone.timedelta(minutes=30)

        active_sessions = (
            TrafficStat.objects
            .filter(created_at__gte=thirty_minutes_ago)
            .values('session_id')
            .annotate(last_active=Max('created_at'))
        )

        data = []
        for session in active_sessions:
            visitor = Visitor.objects.filter(session_key=session['session_id']).select_related('user').first()

            if visitor:
                if visitor.session_ended() or visitor.session_expired():
                    continue

                if visitor.user:
                    user = visitor.user

                    time_on_site_seconds = visitor.time_on_site
                    hours = time_on_site_seconds // 3600
                    minutes = (time_on_site_seconds % 3600) // 60
                    seconds = time_on_site_seconds % 60
                    time_on_site = f"{hours:02}:{minutes:02}:{seconds:02}"

                    user_data = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_staff': user.is_staff,
                        'start_time': visitor.start_time,
                        'time_on_site': time_on_site
                    }
                    user_data['start_time'] = timezone.localtime(visitor.start_time).strftime('%Y-%m-%dT%H:%M:%S.%f')
                else:
                    user_data = {
                        'id': None,
                        'username': 'Guest',
                        'email': None,
                        'is_staff': False
                    }

                last_active_time = timezone.localtime(session['last_active'])
                if last_active_time < thirty_minutes_ago:
                    user_data['is_online'] = False
                else:
                    user_data['is_online'] = True

                data.append({
                    'session_id': session['session_id'],
                    'last_active': last_active_time.strftime('%Y-%m-%dT%H:%M:%S.%f'),
                    **user_data
                })

        return Response({'active_users': data}, status=status.HTTP_200_OK)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserRequestLogView(generics.ListAPIView):
    serializer_class = TrafficStatSerializer
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name='user_id',
                in_=openapi.IN_QUERY,
                description='ID пользователя (для авторизированных пользователей)',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                name='session_id',
                in_=openapi.IN_QUERY,
                description='Session id (для гостей)',
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                name='start_date',
                in_=openapi.IN_QUERY,
                description='Начальная дата в формате YYYY-MM-DD:HH:MM:SS',
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                name='end_date',
                in_=openapi.IN_QUERY,
                description='Конечная дата в формате YYYY-MM-DDT:HH:MM:SS',
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                required=False
            ),
            openapi.Parameter(
                name='url',
                in_=openapi.IN_QUERY,
                description='Фильтрация по url',
                type=openapi.TYPE_STRING,
                required=False
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id')
        session_id = request.query_params.get('session_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        url_filter = request.query_params.get("url")

        if not user_id and not session_id:
            return Response(
                {"error": "Необходимо указать user_id (для пользователей) или session_id (для гостей"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = TrafficStat.objects.all()

        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "Пользователь не найден"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_sessions = Visitor.objects.filter(user=user).values_list("session_key", flat=True)
            queryset = TrafficStat.objects.filter(session_id__in=user_sessions).order_by('-created_at')

        elif session_id:
            queryset = queryset.filter(session_id=session_id).order_by('-created_at')

        if start_date:
            try:
                start_date = timezone.datetime.fromisoformat(start_date)
                start_date = timezone.make_aware(start_date)
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                return Response(
                    {"error": "Некорректный формат start_date"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if end_date:
            try:
                end_date = timezone.datetime.fromisoformat(end_date)
                end_date = timezone.make_aware(end_date)

                if start_date and end_date < start_date:
                    return Response(
                        {"error": "Конечная дата не может быть раньше начальной"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                queryset = queryset.filter(created_at__lte=end_date)
            except ValueError:
                return Response(
                    {"error": "Некорректный формат end_date"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if url_filter:
            queryset = queryset.filter(url__icontains=url_filter)

        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = TrafficStatSerializer(paginated_queryset, many=True)

        total_pages = (paginator.page.paginator.count + paginator.page_size - 1) // paginator.page_size

        response_data = OrderedDict([
            ("count", paginator.page.paginator.count),
            ("total_pages", total_pages),
            ("next", paginator.get_next_link()),
            ("previous", paginator.get_previous_link()),
            ("results", serializer.data),
        ])

        return Response(response_data)


def index(request):
    return render(request, 'traffic/index.html')


class StatsView(TemplateView):
    template_name = "traffic/stats.html"
