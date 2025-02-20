from collections import OrderedDict
from babel.dates import format_date
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now, localtime
from django.views.generic import TemplateView
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .models import TrafficStat
from tracking.models import Visitor
from .serializers import TrafficStatSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Max, F, Avg
from django.utils import timezone
from babel import Locale
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
        queryset = queryset.annotate(hour=TruncHour('created_at')).values('hour').annotate(count=Count('id')).order_by(
            'hour')

        if not queryset.exists():
            return Response(
                {"error": f"Нет данных по дате {selected_date}"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = []
        for stat in queryset:
            unique_registered_users = TrafficStat.objects.filter(
                created_at__hour=stat['hour'].hour,
                created_at__date=selected_date,
                user__isnull=False
            ).values('user').distinct().count()

            unique_guests_count = TrafficStat.objects.filter(
                created_at__hour=stat['hour'].hour,
                created_at__date=selected_date,
                user_id__isnull=True
            ).values('ip_address').distinct().count()

            data.append({
                'hour': stat['hour'].hour,
                'count': stat['count'],
                'unique_registered_users': unique_registered_users,
                'unique_guests': unique_guests_count
            })

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
                start_of_week = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()),
                                                    timezone.get_current_timezone())

            except ValueError:
                return Response(
                    {"error": "Неверный формат недели. Используйте YYYY-WW"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            now = timezone.localtime(timezone.now())

            iso_year, iso_week, iso_weekday = now.isocalendar()

            start_of_week = now - timezone.timedelta(days=iso_weekday - 1)
            start_of_week = timezone.make_aware(datetime.combine(start_of_week.date(), datetime.min.time()),
                                                timezone.get_current_timezone())

        end_of_week = start_of_week + timezone.timedelta(days=6, hours=23, minutes=59, seconds=59)
        end_of_week = timezone.make_aware(datetime.combine(end_of_week.date(), datetime.max.time()),
                                          timezone.get_current_timezone())

        queryset = TrafficStat.objects.filter(created_at__range=(start_of_week, end_of_week))
        queryset = queryset.annotate(day=TruncDay('created_at')).values('day').annotate(count=Count('id')).order_by(
            'day')

        if not queryset.exists():
            return Response(
                {"error": f"Нет данных для недели {week_str}"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = []
        for stat in queryset:
            unique_registered_users = TrafficStat.objects.filter(
                created_at__date=stat['day'],
                user__isnull=False
            ).values('user').distinct().count()

            unique_guests_count = TrafficStat.objects.filter(
                created_at__date=stat['day'],
                user_id__isnull=True
            ).values('ip_address').distinct().count()

            locale = Locale('ru', 'RU')
            day = format_date(stat['day'], format='long', locale=locale)
            day_of_week = format_date(stat['day'], format='EEEE', locale=locale)

            data.append({
                'day': f"{day} {day_of_week}",
                'count': stat['count'],
                'unique_registered_users': unique_registered_users,
                'unique_guests': unique_guests_count
            })

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
        queryset = queryset.annotate(day=TruncDay('created_at')).values('day').annotate(count=Count('id')).order_by(
            'day')

        if not queryset.exists():
            return Response(
                {"error": f"Нет данных для месяца {month_str or selected_month.strftime('%Y-%m')}"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = []
        for stat in queryset:
            unique_registered_users = TrafficStat.objects.filter(
                created_at__month=stat['day'].month,
                user__isnull=False
            ).values('user').distinct().count()

            unique_guests_count = TrafficStat.objects.filter(
                created_at__month=stat['day'].month,
                user_id__isnull=True
            ).values('ip_address').distinct().count()

            locale = Locale('ru', 'RU')
            month = format_date(stat['day'], format='MMMM', locale=locale)
            day = format_date(stat['day'], format='long', locale=locale)

            data.append({
                'month': month,
                'day': day,
                'count': stat['count'],
                'unique_registered_users': unique_registered_users,
                'unique_guests': unique_guests_count
            })

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
        queryset = queryset.annotate(month=TruncMonth('created_at')).values('month').annotate(
            count=Count('id')).order_by('month')

        if not queryset.exists():
            return Response(
                {"error": f"Нет данных для года {year_str or selected_year.year}"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = []
        for stat in queryset:
            unique_registered_users = TrafficStat.objects.filter(
                created_at__month=stat['month'].month,
                user__isnull=False
            ).values('user').distinct().count()

            unique_guests_count = TrafficStat.objects.filter(
                created_at__month=stat['month'].month,
                user_id__isnull=True
            ).values('ip_address').distinct().count()

            locale = Locale('ru', 'RU')
            month = format_date(stat['month'], format='MMMM', locale=locale)

            data.append({
                'month': month,
                'count': stat['count'],
                'unique_registered_users': unique_registered_users,
                'unique_guests': unique_guests_count
            })

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


'''
Функция для облегчения ActiveUsersView и работы с context в html
'''


def get_active_and_registered_users():
    five_minutes_ago = now() - timedelta(minutes=5)

    start_date = now() - timedelta(days=7)
    end_date = now()

    all_users = User.objects.all()

    user_stats = Visitor.objects.user_stats(start_date, end_date)
    user_sessions = {user.id: {'visit_count': user.visit_count,
                               'avg_time_on_site': user.time_on_site
                               } for user in user_stats}

    active_sessions = (
        TrafficStat.objects
        .filter(created_at__gte=five_minutes_ago)
        .values('session_id')
        .annotate(last_active=Max('created_at'))
    )

    active_users_data = {}
    for session in active_sessions:
        visitor = Visitor.objects.filter(session_key=session['session_id']).select_related('user').first()
        if not visitor or not visitor.user:
            continue

        if visitor.session_ended() or visitor.session_expired():
            continue

        user = visitor.user
        time_on_site_seconds = visitor.time_on_site
        time_on_site = f"{time_on_site_seconds // 3600:02}:{(time_on_site_seconds % 3600) // 60:02}:{time_on_site_seconds % 60:02}"

        last_active_time = session['last_active']
        is_online = last_active_time >= five_minutes_ago

        active_users_data[user.id] = {
            'is_online': is_online,
            'time_on_site': time_on_site
        }

    registered_users = []
    for user in all_users:
        session_data = user_sessions.get(user.id, {})
        visit_count = session_data.get('visit_count', 0)
        avg_time_on_site_seconds = session_data.get('avg_time_on_site', timedelta(0))
        if isinstance(avg_time_on_site_seconds, timedelta):
            avg_time_on_site_seconds = avg_time_on_site_seconds.total_seconds()

        avg_time_on_site = (
            f"{int(avg_time_on_site_seconds) // 3600:02}:{(int(avg_time_on_site_seconds) % 3600) // 60:02}:{int(avg_time_on_site_seconds) % 60:02}"
            if avg_time_on_site_seconds else "00:00:00"
        )

        visitor = Visitor.objects.filter(user=user).order_by('-start_time').first()
        if visitor:
            start_time = visitor.start_time
            start_time_local = timezone.localtime(start_time)
        else:
            start_time_local = "Неизвестно"

        user_data = {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'email': user.email,
            'is_staff': user.is_staff,
            'is_online': active_users_data.get(user.id, {}).get('is_online', False),
            'time_on_site': active_users_data.get(user.id, {}).get('time_on_site', '-'),
            'visit_count': visit_count,
            'avg_time_on_site': avg_time_on_site,
            'start_time': start_time_local
        }
        registered_users.append(user_data)

    registered_users.sort(key=lambda x: (x['is_online']), reverse=True)

    return registered_users


class ActiveUsersView(APIView):
    def get(self, request, *args, **kwargs):

        data = get_active_and_registered_users()
        online_users_count = sum(1 for user in data if user['is_online'])

        return Response({'registered_users': data, 'online_users_count': online_users_count}, status=status.HTTP_200_OK)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


def filter_traffic_stats(request, user=None):
    """
    Функция фильтрации запросов по параметрам в запросе
    Может быть использована как в API для swagger, так и для рендеринга страницы user_requests.html
    """
    queryset = TrafficStat.objects.all()

    if user:
        user_sessions = Visitor.objects.filter(user=user).values_list("session_key", flat=True)
        queryset = queryset.filter(session_id__in=user_sessions).order_by('-created_at')

    params = request.GET if hasattr(request, "GET") else request.query_params

    start_date = params.get('start_date')
    if start_date:
        try:
            start_date = timezone.datetime.fromisoformat(start_date)
            start_date = timezone.make_aware(start_date)
            queryset = queryset.filter(created_at__gte=start_date)
        except ValueError:
            raise ValidationError({"error": "Некорректный формат start_date"})

    end_date = params.get('end_date')
    if end_date:
        try:
            end_date = timezone.datetime.fromisoformat(end_date)
            end_date = timezone.make_aware(end_date)
            queryset = queryset.filter(created_at__lte=end_date)
        except ValueError:
            raise ValidationError({"error": "Некорректный формат end_date"})

    url_filter = params.get("url")
    if url_filter:
        queryset = queryset.filter(url__icontains=url_filter)

    return queryset


class UserRequestLogView(generics.ListAPIView):
    serializer_class = TrafficStatSerializer
    pagination_class = StandardResultsSetPagination

    @swagger_auto_schema(
        manual_parameters=[
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
                description='Фильтрация по URL',
                type=openapi.TYPE_STRING,
                required=False
            ),
        ]
    )

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "Данный пользователь не найден"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = filter_traffic_stats(self.request, user)
        return queryset


    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
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

        return Response(response_data, status=status.HTTP_200_OK)


def index(request):
    end_date = now()
    start_date = end_date - timedelta(days=7)

    visitor_stats = Visitor.objects.stats(start_date, end_date)
    user_stats = Visitor.objects.user_stats(start_date, end_date)

    registered_users = get_active_and_registered_users()
    online_users_count = sum(1 for user in registered_users if user['is_online'])

    context = {
        "visitor_stats": visitor_stats,
        "user_stats": user_stats,
        "registered_users": registered_users,
        "online_users_count": online_users_count,
    }

    return render(request, 'traffic/index.html', context)


class StatsView(TemplateView):
    template_name = "traffic/stats.html"


def user_requests(request, user_id):
    user = get_object_or_404(User, id=user_id)

    queryset = filter_traffic_stats(request, user)

    page_number = request.GET.get('page', 1)
    paginator = Paginator(queryset, StandardResultsSetPagination.page_size)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        "user": user,
        "logs": page_obj.object_list,
        "start_date": request.GET.get('start_date'),
        "end_date": request.GET.get('end_date'),
        "url_filter": request.GET.get('url'),
        "total_pages": paginator.num_pages,
        "current_page": page_obj.number,
    }

    return render(request, 'traffic/user_requests.html', context)

