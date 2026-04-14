from django.db import models
from django.conf import settings
from users.models import Shop
from decimal import Decimal


class SubscriptionPlan(models.Model):
    """
    Subscription plans available for pharmacy shops
    """
    PLAN_TYPES = (
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
        ('premium', 'Premium'),
    )
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    
    # Feature limits
    max_users = models.IntegerField(default=1)
    max_inventory_items = models.IntegerField(default=1000)
    max_transactions_per_month = models.IntegerField(default=500)
    
    # Features available
    analytics_dashboard = models.BooleanField(default=False)
    advanced_reporting = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    custom_branding = models.BooleanField(default=False)
    multi_location = models.BooleanField(default=False)
    backup_restore = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['sort_order', 'price_monthly']
    
    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/month"
    
    @property
    def yearly_discount_percent(self):
        monthly_yearly = self.price_monthly * 12
        if monthly_yearly > 0:
            return round((1 - (self.price_yearly / monthly_yearly)) * 100)
        return 0


class Subscription(models.Model):
    """
    Active subscriptions for shops
    """
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Payment'),
        ('trial', 'Free Trial'),
    )
    
    BILLING_CYCLES = (
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    )
    
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='monthly')
    
    # Dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Payment info
    current_amount = models.DecimalField(max_digits=10, decimal_places=2)
    auto_renew = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.shop.name} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        from django.utils import timezone
        return self.status == 'active' and self.end_date > timezone.now()
    
    @property
    def is_trial(self):
        from django.utils import timezone
        return (self.status == 'trial' and 
                self.trial_end_date and 
                self.trial_end_date > timezone.now())
    
    @property
    def days_remaining(self):
        from django.utils import timezone
        if self.end_date > timezone.now():
            return (self.end_date - timezone.now()).days
        return 0


class Payment(models.Model):
    """
    Payment records for subscriptions
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Payment gateway details
    payment_method = models.CharField(max_length=50)  # stripe, paypal, bkash, etc.
    transaction_id = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.subscription.shop.name} - ${self.amount} ({self.status})"


class FeatureUsage(models.Model):
    """
    Track feature usage for billing and limits
    """
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='feature_usage')
    month_year = models.CharField(max_length=7)  # Format: YYYY-MM
    
    # Usage counters
    transactions_count = models.IntegerField(default=0)
    inventory_items_count = models.IntegerField(default=0)
    active_users_count = models.IntegerField(default=0)
    api_calls_count = models.IntegerField(default=0)
    reports_generated = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['shop', 'month_year']
    
    def __str__(self):
        return f"{self.shop.name} - {self.month_year}"
