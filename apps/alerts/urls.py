from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlertViewSet,AlertTriggerViewSet

router = DefaultRouter()
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'alert-triggers', AlertTriggerViewSet, basename='alert-trigger')

urlpatterns = [
    path('', include(router.urls)),
]
