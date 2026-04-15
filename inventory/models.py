from charset_normalizer import md
from django.db import models
from django.conf import settings
from catalog.models import MasterCatalog
from decimal import Decimal


class ShopCustomMedicine(models.Model):
    """Custom medicines added by shop owners (not in master catalog)"""
    DOSAGE_FORMS = [
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('powder', 'Powder'),
        ('ointment', 'Ointment'),
        ('cream', 'Cream'),
        ('drops', 'Drops'),
        ('inhaler', 'Inhaler'),
        ('other', 'Other'),
    ]

    shop = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_medicines')
    brand_name = models.CharField(max_length=200)
    generic = models.CharField(max_length=200)
    strength = models.CharField(max_length=100)
    dosage_form = models.CharField(max_length=50, choices=DOSAGE_FORMS, default='tablet')
    manufacturer = models.CharField(max_length=200, blank=True)
    suggested_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_custom_medicines'
        verbose_name = 'Shop Custom Medicine'
        verbose_name_plural = 'Shop Custom Medicines'
        unique_together = ['shop', 'brand_name', 'strength']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop']),
            models.Index(fields=['brand_name']),
        ]

    def __str__(self):
        return f"{self.shop.username} - {self.brand_name} ({self.strength})"


class ShopInventory(models.Model):
    """Shop-specific inventory linking to Master Catalog"""
    shop = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inventory_items')
    master_medicine = models.ForeignKey(MasterCatalog, on_delete=models.CASCADE, related_name='shop_inventories')
    local_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=100)
    low_stock_threshold = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_inventory'
        verbose_name = 'Shop Inventory'
        verbose_name_plural = 'Shop Inventory'
        unique_together = ['shop', 'master_medicine', 'batch_number']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop']),
            models.Index(fields=['master_medicine']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.shop.shop.name if self.shop.shop else self.shop.username} - {self.master_medicine.brand_name}"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()


class ShopCustomMedicineInventory(models.Model):
    """Shop-specific inventory for custom medicines (not in master catalog)"""
    shop = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_inventory_items')
    custom_medicine = models.ForeignKey(ShopCustomMedicine, on_delete=models.CASCADE, related_name='shop_inventories')
    local_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    expiry_date = models.DateField()
    batch_number = models.CharField(max_length=100)
    low_stock_threshold = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shop_custom_medicine_inventory'
        verbose_name = 'Shop Custom Medicine Inventory'
        verbose_name_plural = 'Shop Custom Medicine Inventories'
        unique_together = ['shop', 'custom_medicine', 'batch_number']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop']),
            models.Index(fields=['custom_medicine']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.shop.shop.name if self.shop.shop else self.shop.username} - {self.custom_medicine.brand_name}"

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()


class StockAdjustment(models.Model):
    """Track stock adjustments for audit purposes"""
    ADJUSTMENT_TYPES = [
        ('purchase', 'Purchase'),
        ('sale', 'Sale'),
        ('return', 'Return'),
        ('damage', 'Damage'),
        ('adjustment', 'Manual Adjustment'),
    ]

    inventory = models.ForeignKey(ShopInventory, on_delete=models.CASCADE, related_name='adjustments', null=True, blank=True)
    custom_inventory = models.ForeignKey(ShopCustomMedicineInventory, on_delete=models.CASCADE, related_name='adjustments', null=True, blank=True)
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity = models.IntegerField()
    previous_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    reason = models.TextField(blank=True)
    adjusted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='stock_adjustments')
    adjusted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_adjustments'
        verbose_name = 'Stock Adjustment'
        verbose_name_plural = 'Stock Adjustments'
        ordering = ['-adjusted_at']

    def __str__(self):
        if self.inventory:
            return f"{self.inventory.master_medicine.brand_name} - {self.adjustment_type} ({self.quantity})"
        elif self.custom_inventory:
            return f"{self.custom_inventory.custom_medicine.brand_name} - {self.adjustment_type} ({self.quantity})"
        return f"Stock Adjustment - {self.adjustment_type} ({self.quantity})"
