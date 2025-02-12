from rest_framework import serializers
from .models import TrafficStat


class TrafficStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficStat
        fields = '__all__'
