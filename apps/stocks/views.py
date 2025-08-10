from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated,AllowAny
from .models import Stock, PriceSnapshot
from .serializers import StockSerializer, PriceSnapshotSerializer

# Create your views here.

class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [AllowAny]

class PriceSnapshotViewSet(viewsets.ModelViewSet):
    queryset = PriceSnapshot.objects.all()
    serializer_class = PriceSnapshotSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        stock_id = self.request.query_params.get('stock')
        if stock_id:
            qs = qs.filter(stock_id=stock_id)
        return qs