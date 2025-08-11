from django.urls import path,include
from .views import StockViewSet, PriceSnapshotViewSet


urlpatterns = [
    path('', StockViewSet.as_view({'get': 'list', 'post': 'create'}), name='stock-list'),
    path('<int:pk>/', StockViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='stock-detail'),
    path('price_snapshots/', PriceSnapshotViewSet.as_view({'get': 'list', 'post': 'create'}), name='snapshot-list'),
    path('price_snapshots/<int:pk>/', PriceSnapshotViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='snapshot-detail'),
]
