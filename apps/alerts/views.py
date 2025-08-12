from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from apps.alerts.serializers import AlertSerializer, AlertTriggerSerializer 
from .models import Alert, AlertTrigger

# Create your views here.

class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
class AlertTriggerViewSet(viewsets.ModelViewSet):
    serializer_class = AlertTriggerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AlertTrigger.objects.filter(alert__user=self.request.user)