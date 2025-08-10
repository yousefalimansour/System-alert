from django.db import models
from django.conf import settings
from apps.stocks.models import Stock

# Create your models here.

class Alert(models.Model):
    Alert_TYPE_CHOICES = [
        ('threshold', 'Threshold'),
        ('duration', 'Duration'),
    ]
    OPERATOR_CHOICES = [
        ('gt', '>'),
        ('lt', '<'),
        ('eq', '='),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alerts')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='alerts')
    name = models.CharField(max_length=200, blank=True)
    alert_type = models.CharField(max_length=20, choices=Alert_TYPE_CHOICES)
    operator = models.CharField(max_length=2, choices=OPERATOR_CHOICES)
    threshold = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)

    state_is_open = models.BooleanField(default=True)
    state_started = models.DateTimeField(null=True, blank=True)
    last_price = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['alert_type', 'stock', 'is_active']),
        ]

    def __str__(self):
        return f"Alert for {self.user} on {self.stock} - {self.alert_type}"

class AlertTrigger(models.Model):
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name='triggers')
    triggered_at = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=20, decimal_places=4)
    message = models.TextField(blank=True)

    class Meta:
        ordering = ['-triggered_at']

    def __str__(self):
        return f"Trigger for {self.alert} at {self.triggered_at}"