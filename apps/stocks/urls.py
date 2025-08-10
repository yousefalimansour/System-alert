from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import StockViewSet ,PriceSnapshotViewSet 

router = DefaultRouter()
router.register(r'stocks', StockViewSet,basename='stock')
router.register(r'price_snapshots', PriceSnapshotViewSet,basename='snapshot')

urlpatterns = [
    path('', include(router.urls)),
]
