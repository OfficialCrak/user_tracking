from django.urls import path
from .views import DailyTrafficStats, WeeklyTrafficStats, MonthlyTrafficStats, YearlyTrafficStats

urlpatterns = [
    path('daily/', DailyTrafficStats.as_view(), name='daily-traffic-stats'),
    path('weekly/', WeeklyTrafficStats.as_view(), name='weekly-traffic-stats'),
    path('monthly/', MonthlyTrafficStats.as_view(), name='monthly-traffic-stats'),
    path('yearly/', YearlyTrafficStats.as_view(), name='yearly-traffic-stats'),
]
