from django.db import models
from django.utils import timezone
from users.models import Shop
from catalog.models import MasterCatalog
from sales.models import Transaction


class AnalyticsSnapshot(models.Model):
    """
    Daily analytics snapshots for performance optimization
    """
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='analytics_snapshots')
    date = models.DateField()
    
    # Daily metrics
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    unique_customers = models.IntegerField(default=0)
    
    # Inventory metrics
    total_inventory_items = models.IntegerField(default=0)
    low_stock_items = models.IntegerField(default=0)
    expired_items = models.IntegerField(default=0)
    
    # Performance metrics
    average_transaction_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    top_selling_medicine_id = models.IntegerField(null=True, blank=True)
    top_selling_medicine_quantity = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['shop', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.shop.name} - {self.date}"


class SalesAnalytics(models.Model):
    """
    Detailed sales analytics for reporting
    """
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    medicine = models.ForeignKey(MasterCatalog, on_delete=models.CASCADE)
    date = models.DateField()
    
    quantity_sold = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['shop', 'medicine', 'date']
        ordering = ['-date', '-quantity_sold']
    
    def __str__(self):
        return f"{self.shop.name} - {self.medicine.brand_name} - {self.date}"


class InventoryAnalytics(models.Model):
    """
    Inventory movement and trends
    """
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    medicine = models.ForeignKey(MasterCatalog, on_delete=models.CASCADE)
    date = models.DateField()
    
    opening_stock = models.IntegerField(default=0)
    closing_stock = models.IntegerField(default=0)
    stock_added = models.IntegerField(default=0)
    stock_sold = models.IntegerField(default=0)
    stock_adjusted = models.IntegerField(default=0)  # Wastage, returns, etc.
    
    class Meta:
        unique_together = ['shop', 'medicine', 'date']
        ordering = ['-date']
