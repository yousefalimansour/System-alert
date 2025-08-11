from rest_framework import serializers
from apps.stocks.models import Stock
from apps.stocks.serializers import StockSerializer
from .models import Alert ,AlertTrigger


class AlertSerializer(serializers.ModelSerializer):
    stock = serializers.PrimaryKeyRelatedField(queryset=Stock.objects.all())
    stock_details = StockSerializer(source='stock', read_only=True)

    class Meta:
        model = Alert
        fields = (
            'id', 'user', 'stock', 'stock_details', 'name', 'alert_type', 'operator',
            'threshold', 'duration_minutes', 'state_is_open', 'state_started',
            'last_price', 'is_active', 'created_at', 'last_triggered_at'
        )
        read_only_fields = ('user', 'state_is_open', 'state_started', 'last_price', 'created_at', 'last_triggered_at')

    def validate(self, data):
        alert_type = data.get('alert_type')
        duration = data.get('duration')
        threshold = data.get('threshold')

        if alert_type == 'threshold' and (threshold is None or duration is None):
            raise serializers.ValidationError("Threshold alerts require both threshold and duration to be set.")
        if alert_type == 'duration' and (duration is None):
            raise serializers.ValidationError("Duration alerts require duration to be set and threshold must be None.")

        return data


class AlertTriggerSerializer(serializers.ModelSerializer):
    alert = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = AlertTrigger
        fields = (
            'id', 'alert','triggered_at','price','message'
        )
