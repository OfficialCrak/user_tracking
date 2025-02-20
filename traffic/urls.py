from django.urls import path
from .views import DailyTrafficStats, WeeklyTrafficStats, MonthlyTrafficStats, YearlyTrafficStats, ActiveUsersView, \
    UserRequestLogView, index, StatsView, user_requests

urlpatterns = [
    path('daily/', DailyTrafficStats.as_view(), name='daily-traffic-stats'),
    path('weekly/', WeeklyTrafficStats.as_view(), name='weekly-traffic-stats'),
    path('monthly/', MonthlyTrafficStats.as_view(), name='monthly-traffic-stats'),
    path('yearly/', YearlyTrafficStats.as_view(), name='yearly-traffic-stats'),
    path('active-users/', ActiveUsersView.as_view(), name='active-users'),
    path('user-requests/<int:user_id>/', UserRequestLogView.as_view(), name='user_log_requests'),

    path('', index, name='index-monitoring'),
    path('stats/', StatsView.as_view(), name='stats'),
    path('user_log_requests/<int:user_id>/', user_requests, name='user-requests'),
]
