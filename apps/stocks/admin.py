from django.contrib import admin
from .models import Stock , PriceSnapshot
# Register your models here.

class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'created_at')
    search_fields = ('ticker', 'name')

class PriceSnapshotAdmin(admin.ModelAdmin):
    list_display = ('stock', 'price', 'timestamp')
    list_filter = ('stock',)
    ordering = ('-timestamp',)

admin.site.register(Stock, StockAdmin)
admin.site.register(PriceSnapshot, PriceSnapshotAdmin)  
