from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class Shop(models.Model):
    """Shop/Pharmacy entity"""
    SUBSCRIPTION_TIERS = [
        ('BASIC', 'Basic'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100, unique=True)
    dgda_license = models.CharField(max_length=100, blank=True, help_text="DGDA regulatory license number")
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    subscription_tier = models.CharField(max_length=20, choices=SUBSCRIPTION_TIERS, default='BASIC')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shops'
        verbose_name = 'Shop'
        verbose_name_plural = 'Shops'
        indexes = [
            models.Index(fields=['license_number']),
            models.Index(fields=['dgda_license']),
        ]

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom User model with RBAC"""
    ROLE_CHOICES = settings.ROLE_CHOICES

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=settings.ROLE_SHOP_WORKER)
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff')
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['shop']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == settings.ROLE_SUPER_ADMIN

    @property
    def is_shop_owner(self):
        return self.role == settings.ROLE_SHOP_OWNER

    @property
    def is_shop_worker(self):
        return self.role == settings.ROLE_SHOP_WORKER
