from django.db import models

# Create your models here.

class Stock(models.Model):
    ticker = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ticker
    

class PriceSnapshot(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='snapshots')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.stock.ticker} - {self.price} ({self.timestamp})"