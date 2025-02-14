from rest_framework import serializers
from .models import TrafficStat


class TrafficStatSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S')

    class Meta:
        model = TrafficStat
        fields = '__all__'
