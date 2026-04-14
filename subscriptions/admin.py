from django.contrib import admin
from .models import SubscriptionPlan, Subscription, Payment, FeatureUsage


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price_monthly', 'price_yearly', 'max_users', 'is_active']
    list_filter = ['plan_type', 'is_active']
    ordering = ['sort_order', 'price_monthly']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['shop', 'plan', 'status', 'billing_cycle', 'start_date', 'end_date', 'days_remaining']
    list_filter = ['status', 'billing_cycle', 'plan']
    search_fields = ['shop__name', 'shop__license_number']
    readonly_fields = ['created_at', 'updated_at']
    
    def days_remaining(self, obj):
        return obj.days_remaining
    days_remaining.short_description = 'Days Left'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method']
    search_fields = ['subscription__shop__name', 'transaction_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FeatureUsage)
class FeatureUsageAdmin(admin.ModelAdmin):
    list_display = ['shop', 'month_year', 'transactions_count', 'inventory_items_count', 'active_users_count']
    list_filter = ['month_year']
    search_fields = ['shop__name']
    readonly_fields = ['created_at', 'updated_at']
