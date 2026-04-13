from django.db import models
from django.conf import settings
from inventory.models import ShopInventory


class Customer(models.Model):
    """Customer model for tracking sales and dues"""
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    shop = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customers'
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def total_due(self):
        return self.dues.filter(is_paid=False).aggregate(models.Sum('amount'))['amount__sum'] or 0


class Transaction(models.Model):
    """Transaction/Invoice model"""
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Payment'),
        ('credit', 'Credit/Due'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True)
    shop = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['shop']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"INV-{self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last_invoice = Transaction.objects.filter(
                invoice_number__startswith=date_str
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.invoice_number = f"{date_str}-{new_num:04d}"
        
        super().save(*args, **kwargs)


class TransactionItem(models.Model):
    """Individual items in a transaction"""
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    inventory = models.ForeignKey(ShopInventory, on_delete=models.SET_NULL, null=True, related_name='transaction_items')
    medicine_name = models.CharField(max_length=200)  # Store name for history
    generic_name = models.CharField(max_length=200, blank=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    batch_number = models.CharField(max_length=100)

    class Meta:
        db_table = 'transaction_items'
        verbose_name = 'Transaction Item'
        verbose_name_plural = 'Transaction Items'

    def __str__(self):
        return f"{self.medicine_name} x {self.quantity}"


class CustomerDue(models.Model):
    """Track customer dues/balances"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='dues')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='dues')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'customer_dues'
        verbose_name = 'Customer Due'
        verbose_name_plural = 'Customer Dues'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} - {self.amount}"
