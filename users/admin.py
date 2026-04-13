from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Shop


class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'shop', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'shop', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'shop', 'phone')}),
    )


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_number', 'dgda_license', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'license_number']
