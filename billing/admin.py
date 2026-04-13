from django.contrib import admin
from .models import Subscription, Invoice


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['shop', 'plan', 'status', 'current_period_end']
    list_filter = ['plan', 'status']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'amount', 'status', 'due_date']
    list_filter = ['status']
