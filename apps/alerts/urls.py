from django.urls import path
from .views import AlertViewSet, AlertTriggerViewSet

urlpatterns = [
    path('', AlertViewSet.as_view({'get': 'list', 'post': 'create'}), name='alert-list'),
    path('<int:pk>/', AlertViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='alert-detail'),
    path('triggers/', AlertTriggerViewSet.as_view({'get': 'list', 'post': 'create'}), name='alert-trigger-list'),
    path('triggers/<int:pk>/', AlertTriggerViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='alert-trigger-detail'),
]
