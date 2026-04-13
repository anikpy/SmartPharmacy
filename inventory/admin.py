from django.contrib import admin
from .models import ShopInventory, StockAdjustment


@admin.register(ShopInventory)
class ShopInventoryAdmin(admin.ModelAdmin):
    list_display = ['shop', 'master_medicine', 'local_price', 'stock_quantity', 'expiry_date', 'batch_number', 'is_active']
    list_filter = ['shop', 'expiry_date', 'is_active']
    search_fields = ['master_medicine__brand_name', 'master_medicine__generic', 'batch_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['inventory', 'adjustment_type', 'quantity', 'previous_quantity', 'new_quantity', 'adjusted_by', 'adjusted_at']
    list_filter = ['adjustment_type', 'adjusted_at']
    search_fields = ['inventory__master_medicine__brand_name', 'reason']
    readonly_fields = ['adjusted_at']
