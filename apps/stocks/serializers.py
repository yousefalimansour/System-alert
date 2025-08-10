from rest_framework import serializers
from .models import Stock , PriceSnapshot

class PriceSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceSnapshot
        fields = ('id', 'stock', 'price', 'timestamp')
        read_only_fields = ('id', 'timestamp')

class StockSerializer(serializers.ModelSerializer):
    latest_price_snapshot = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = ('id', 'ticker', 'name', 'latest_price_snapshot')

    def get_latest_price_snapshot(self, obj):
            snap = obj.snapshots.first()
            if snap:
                return PriceSnapshotSerializer(snap).data
            return None
