from django.contrib import admin
from .models import MasterCatalog


@admin.register(MasterCatalog)
class MasterCatalogAdmin(admin.ModelAdmin):
    list_display = ['brand_name', 'generic', 'strength', 'dosage_form', 'manufacturer', 'type', 'is_active']
    list_filter = ['type', 'dosage_form', 'manufacturer', 'is_active']
    search_fields = ['brand_name', 'generic', 'manufacturer']
    list_editable = ['is_active']
    readonly_fields = ['brand_id', 'slug', 'created_at', 'updated_at']
