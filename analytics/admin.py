from django.contrib import admin
from .models import AnalyticsSnapshot, SalesAnalytics, InventoryAnalytics


@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ['shop', 'date', 'total_sales', 'total_transactions', 'total_inventory_items']
    list_filter = ['date', 'shop']
    ordering = ['-date']


@admin.register(SalesAnalytics)
class SalesAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['shop', 'medicine', 'date', 'quantity_sold', 'total_revenue']
    list_filter = ['date', 'shop']
    ordering = ['-date', '-quantity_sold']


@admin.register(InventoryAnalytics)
class InventoryAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['shop', 'medicine', 'date', 'opening_stock', 'closing_stock']
    list_filter = ['date', 'shop']
    ordering = ['-date']
