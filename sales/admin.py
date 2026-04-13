from django.contrib import admin
from .models import Customer, Transaction, TransactionItem, CustomerDue


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'shop', 'created_at']
    list_filter = ['shop', 'created_at']
    search_fields = ['name', 'phone']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'shop', 'customer', 'total', 'payment_method', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['invoice_number', 'customer__name']
    readonly_fields = ['invoice_number', 'created_at']


@admin.register(TransactionItem)
class TransactionItemAdmin(admin.ModelAdmin):
    list_display = ['medicine_name', 'quantity', 'unit_price', 'total_price', 'transaction']
    search_fields = ['medicine_name', 'generic_name']


@admin.register(CustomerDue)
class CustomerDueAdmin(admin.ModelAdmin):
    list_display = ['customer', 'amount', 'is_paid', 'paid_date', 'created_at']
    list_filter = ['is_paid', 'created_at']
    search_fields = ['customer__name']
