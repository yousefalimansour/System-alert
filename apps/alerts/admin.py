from django.contrib import admin
from .models import Alert , AlertTrigger    
# Register your models here.

class AlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'threshold', 'created_at', 'is_active',)
    search_fields = ('user__username', 'stock__name')
    list_filter = ('alert_type','is_active','operator')

class AlertTriggerAdmin(admin.ModelAdmin):
    list_display = ('alert', 'triggered_at', 'price')
    list_filter = ('triggered_at',)

admin.site.register(Alert, AlertAdmin)
admin.site.register(AlertTrigger, AlertTriggerAdmin)
