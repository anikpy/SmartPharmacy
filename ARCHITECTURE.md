# Smart Pharmacy SaaS - Architecture Documentation

## Tech Stack

### Backend
- **Django 5.0** - Web framework
- **Django REST Framework (DRF)** - API layer
- **PostgreSQL 15** - Database with Row Level Security (RLS)
- **Celery + Redis** - Async tasks (notifications, expiry alerts)
- **Stripe** - Subscription billing
- **Pandas** - Inventory analytics and predictions

### Frontend
- **Next.js 15** (App Router) - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Shadcn UI** - Component library
- **React Query (TanStack Query)** - Data fetching
- **Zustand** - State management
- **React Hook Form** - Form handling

## Project Structure

```
smart-pharmacy/
├── backend/                          # Django REST API
│   ├── config/                       # Django settings
│   │   ├── settings/
│   │   │   ├── base.py              # Base settings
│   │   │   ├── development.py       # Dev settings
│   │   │   ├── production.py        # Prod settings
│   │   │   └── test.py              # Test settings
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   │   ├── users/                   # User authentication & RBAC
│   │   │   ├── models.py            # User, Shop, Role
│   │   │   ├── serializers.py       # DRF serializers
│   │   │   ├── views.py             # API viewsets
│   │   │   ├── permissions.py       # Custom permissions
│   │   │   └── urls.py
│   │   ├── catalog/                 # Master medicine catalog
│   │   │   ├── models.py            # MasterMedicine
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── inventory/               # Shop inventory management
│   │   │   ├── models.py            # ShopInventory, StockAdjustment
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py          # Business logic (expiry, predictions)
│   │   │   └── urls.py
│   │   ├── sales/                   # POS & transactions
│   │   │   ├── models.py            # Transaction, TransactionItem, Customer
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── billing/                 # Subscriptions & payments
│   │   │   ├── models.py            # Subscription, Invoice, Payment
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── webhooks.py          # Stripe webhooks
│   │   │   └── urls.py
│   │   ├── notifications/           # CRM & alerts
│   │   │   ├── models.py            # Notification, NotificationTemplate
│   │   │   ├── services.py          # WhatsApp/SMS services
│   │   │   ├── tasks.py             # Celery tasks
│   │   │   └── urls.py
│   │   ├── compliance/              # DGDA regulatory compliance
│   │   │   ├── models.py            # AuditLog, ComplianceRecord
│   │   │   ├── serializers.py
│   │   │   └── views.py
│   │   └── analytics/               # Platform analytics
│   │       ├── services.py          # Analytics calculations
│   │       └── views.py
│   ├── core/                        # Shared utilities
│   │   ├── permissions.py           # Base permissions
│   │   ├── pagination.py            # Custom pagination
│   │   ├── filters.py               # Custom filters
│   │   └── exceptions.py            # Custom exceptions
│   ├── media/                       # User uploads (prescriptions)
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                        # Next.js frontend
│   ├── app/
│   │   ├── (auth)/                  # Auth group
│   │   │   ├── login/
│   │   │   └── register/
│   │   ├── (dashboard)/             # Dashboard group
│   │   │   ├── super-admin/
│   │   │   ├── shop-owner/
│   │   │   └── shop-worker/
│   │   ├── (pos)/                   # POS group
│   │   │   └── pos/
│   │   ├── api/                     # API routes (if needed)
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/                      # Shadcn UI components
│   │   ├── pos/                     # POS-specific components
│   │   ├── inventory/               # Inventory components
│   │   └── shared/                  # Shared components
│   ├── lib/
│   │   ├── api.ts                   # API client
│   │   ├── auth.ts                  # Auth utilities
│   │   └── utils.ts                 # Utilities
│   ├── hooks/                       # Custom React hooks
│   ├── stores/                      # Zustand stores
│   ├── types/                       # TypeScript types
│   ├── public/
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
├── docker-compose.yml               # Docker orchestration
└── .env.example                     # Environment variables template
```

## Database Schema

### Users & Authentication

```python
# apps/users/models.py
class Shop(models.Model):
    """Shop/Pharmacy entity"""
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=200)
    license_number = CharField(max_length=100, unique=True)
    dgda_license = CharField(max_length=100)  # DGDA compliance
    address = TextField()
    phone = CharField(max_length=20)
    email = EmailField()
    is_active = BooleanField(default=True)
    subscription_tier = CharField(...)  # basic, pro, enterprise
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

class User(AbstractUser):
    """Custom user with RBAC"""
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('SHOP_OWNER', 'Shop Owner'),
        ('SHOP_WORKER', 'Shop Worker'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    role = CharField(max_length=20, choices=ROLE_CHOICES)
    shop = ForeignKey(Shop, on_delete=CASCADE, null=True, related_name='staff')
    phone = CharField(max_length=20)
    avatar = ImageField(upload_to='avatars/', null=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            Index(fields=['shop']),
            Index(fields=['role']),
        ]
```

### Master Catalog

```python
# apps/catalog/models.py
class MasterMedicine(models.Model):
    """Global medicine catalog (managed by Super Admin)"""
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    brand_name = CharField(max_length=200, db_index=True)
    generic_name = CharField(max_length=200, db_index=True)
    strength = CharField(max_length=100)
    dosage_form = CharField(...)  # tablet, capsule, syrup, etc.
    manufacturer = CharField(max_length=200)
    category = CharField(...)  # antibiotic, analgesic, etc.
    prescription_required = BooleanField(default=True)
    is_controlled_substance = BooleanField(default=False)
    dgda_approved = BooleanField(default=True)  # Regulatory compliance
    active_ingredients = JSONField()  # List of ingredients
    contraindications = TextField(blank=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            Index(fields=['brand_name']),
            Index(fields=['generic_name']),
            Index(fields=['manufacturer']),
            GinIndex(fields=['brand_name', 'generic_name']),  # Full-text search
        ]
```

### Shop Inventory

```python
# apps/inventory/models.py
class ShopInventory(models.Model):
    """Shop-specific inventory with batches"""
    EXPIRY_STATUS = [
        ('GREEN', 'Good (>6 months)'),
        ('YELLOW', 'Warning (1-6 months)'),
        ('RED', 'Critical (<1 month)'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    shop = ForeignKey(Shop, on_delete=CASCADE, related_name='inventory')
    master_medicine = ForeignKey(MasterMedicine, on_delete=CASCADE, related_name='shop_inventories')
    
    # Pricing
    purchase_price = DecimalField(max_digits=10, decimal_places=2)
    selling_price = DecimalField(max_digits=10, decimal_places=2)
    
    # Stock
    current_stock = IntegerField(default=0)
    batch_number = CharField(max_length=100)
    expiry_date = DateField()
    expiry_status = CharField(max_length=10, choices=EXPIRY_STATUS)
    
    # Low stock prediction
    reorder_level = IntegerField(default=10)
    predicted_stockout_date = DateField(null=True)
    sales_velocity = FloatField(default=0)  # Units sold per day
    
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['shop', 'master_medicine', 'batch_number']
        indexes = [
            Index(fields=['shop', 'expiry_date']),
            Index(fields=['shop', 'expiry_status']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate expiry status
        self.expiry_status = self._calculate_expiry_status()
        super().save(*args, **kwargs)

class StockAdjustment(models.Model):
    """Audit log for stock changes (DGDA compliance)"""
    ADJUSTMENT_TYPES = [
        ('PURCHASE', 'Purchase'),
        ('SALE', 'Sale'),
        ('RETURN', 'Return'),
        ('DAMAGE', 'Damage/Loss'),
        ('EXPIRED', 'Expired'),
        ('ADJUSTMENT', 'Manual Adjustment'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    inventory = ForeignKey(ShopInventory, on_delete=CASCADE, related_name='adjustments')
    adjustment_type = CharField(max_length=20, choices=ADJUSTMENT_TYPES)
    quantity_before = IntegerField()
    quantity_after = IntegerField()
    quantity_change = IntegerField()
    reason = TextField()
    adjusted_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    adjusted_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            Index(fields=['inventory', 'adjusted_at']),
        ]
```

### Transactions

```python
# apps/sales/models.py
class Customer(models.Model):
    """Customer CRM"""
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    shop = ForeignKey(Shop, on_delete=CASCADE, related_name='customers')
    name = CharField(max_length=200)
    phone = CharField(max_length=20, unique=True)
    email = EmailField(blank=True)
    address = TextField(blank=True)
    date_of_birth = DateField(null=True)
    allergies = JSONField(default=list)  # List of allergies
    chronic_conditions = JSONField(default=list)
    total_due = DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['shop', 'phone']

class Transaction(models.Model):
    """Sales transaction/invoice"""
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CARD', 'Card'),
        ('MOBILE', 'Mobile Payment'),
        ('CREDIT', 'Credit/Due'),
        ('INSURANCE', 'Insurance'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    invoice_number = CharField(max_length=50, unique=True)
    shop = ForeignKey(Shop, on_delete=CASCADE, related_name='transactions')
    customer = ForeignKey(Customer, on_delete=SET_NULL, null=True, related_name='transactions')
    
    subtotal = DecimalField(max_digits=10, decimal_places=2)
    discount = DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = DecimalField(max_digits=10, decimal_places=2, default=0)
    total = DecimalField(max_digits=10, decimal_places=2)
    
    payment_method = CharField(max_length=20, choices=PAYMENT_METHODS)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    
    prescription_image = ImageField(upload_to='prescriptions/', null=True)  # Prescription attachment
    notes = TextField(blank=True)
    
    created_by = ForeignKey(User, on_delete=SET_NULL, null=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            Index(fields=['shop', 'created_at']),
            Index(fields=['invoice_number']),
        ]

class TransactionItem(models.Model):
    """Transaction line items"""
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    transaction = ForeignKey(Transaction, on_delete=CASCADE, related_name='items')
    inventory = ForeignKey(ShopInventory, on_delete=SET_NULL, null=True)
    
    medicine_name = CharField(max_length=200)
    generic_name = CharField(max_length=200)
    batch_number = CharField(max_length=100)
    quantity = IntegerField()
    unit_price = DecimalField(max_digits=10, decimal_places=2)
    total_price = DecimalField(max_digits=10, decimal_places=2)
    is_substitute = BooleanField(default=False)  # If this was a substitute
```

### Billing & Subscriptions

```python
# apps/billing/models.py
class Subscription(models.Model):
    """Shop subscription (Stripe-ready)"""
    PLAN_CHOICES = [
        ('BASIC', 'Basic'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    shop = OneToOneField(Shop, on_delete=CASCADE, related_name='subscription')
    plan = CharField(max_length=20, choices=PLAN_CHOICES)
    stripe_customer_id = CharField(max_length=100, unique=True)
    stripe_subscription_id = CharField(max_length=100, unique=True)
    status = CharField(...)  # active, past_due, cancelled
    current_period_start = DateField()
    current_period_end = DateField()
    cancel_at_period_end = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

class Invoice(models.Model):
    """Billing invoices"""
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    subscription = ForeignKey(Subscription, on_delete=CASCADE, related_name='invoices')
    stripe_invoice_id = CharField(max_length=100, unique=True)
    amount = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(...)  # draft, open, paid, void
    due_date = DateField()
    paid_at = DateTimeField(null=True)
    created_at = DateTimeField(auto_now_add=True)
```

## Multi-Tenancy Strategy

### 1. Database-Level Isolation (PostgreSQL RLS)
```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE shop_inventory ENABLE ROW LEVEL SECURITY;

-- Policy: Shop owners can only see their own inventory
CREATE POLICY shop_isolation ON shop_inventory
    USING (shop_id = current_setting('app.current_shop_id')::UUID);

-- Set shop context in middleware
SET app.current_shop_id = 'uuid-here';
```

### 2. Application-Level Filtering (DRF)
```python
# core/permissions.py
class IsShopOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'SHOP_OWNER'
    
    def has_object_permission(self, request, view, obj):
        return obj.shop == request.user.shop

# Views automatically filter by shop
class ShopInventoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsShopOwner]
    
    def get_queryset(self):
        return ShopInventory.objects.filter(shop=self.request.user.shop)
```

### 3. Tenant Context Middleware
```python
# core/middleware.py
class TenantContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.shop:
            # Set PostgreSQL session variable for RLS
            with connection.cursor() as cursor:
                cursor.execute(
                    "SET app.current_shop_id = %s",
                    [str(request.user.shop.id)]
                )
        return self.get_response(request)
```

## API Design - POS Endpoints

### Base URL: `/api/v1/`

```python
# apps/sales/urls.py
urlpatterns = [
    # POS Operations
    path('pos/search/', POSMedicineSearchView.as_view(), name='pos-search'),
    path('pos/cart/', CartViewSet.as_view({'get': 'list', 'post': 'create'}), name='cart'),
    path('pos/cart/<uuid:pk>/', CartViewSet.as_view({'delete': 'destroy'}), name='cart-detail'),
    path('pos/transaction/', TransactionViewSet.as_view({'post': 'create'}), name='create-transaction'),
    path('pos/transaction/<uuid:pk>/', TransactionViewSet.as_view({'get': 'retrieve'}), name='transaction-detail'),
    path('pos/substitutes/<uuid:medicine_id>/', SubstituteSearchView.as_view(), name='substitutes'),
    
    # Inventory
    path('inventory/', ShopInventoryViewSet.as_view({'get': 'list', 'post': 'create'}), name='inventory'),
    path('inventory/<uuid:pk>/', ShopInventoryViewSet.as_view({'get': 'retrieve', 'put': 'update'}), name='inventory-detail'),
    path('inventory/low-stock/', LowStockAlertView.as_view(), name='low-stock'),
    path('inventory/expiry-alerts/', ExpiryAlertView.as_view(), name='expiry-alerts'),
]
```

### POS Search Endpoint
```python
# GET /api/v1/pos/search/?q=paracetamol
{
    "results": [
        {
            "id": "uuid",
            "medicine_name": "Paracetamol 500mg",
            "generic_name": "Paracetamol",
            "strength": "500mg",
            "stock": 150,
            "price": 2.50,
            "expiry_date": "2025-12-31",
            "expiry_status": "GREEN",
            "batch_number": "B001"
        }
    ]
}
```

### Cart Operations
```python
# POST /api/v1/pos/cart/
{
    "inventory_id": "uuid",
    "quantity": 2
}

# GET /api/v1/pos/cart/
{
    "items": [
        {
            "inventory_id": "uuid",
            "medicine_name": "Paracetamol 500mg",
            "quantity": 2,
            "unit_price": 2.50,
            "total": 5.00
        }
    ],
    "subtotal": 5.00,
    "tax": 0.00,
    "total": 5.00
}
```

### Create Transaction
```python
# POST /api/v1/pos/transaction/
{
    "customer_id": "uuid",  # optional
    "payment_method": "CASH",
    "prescription_image": "base64_or_url",
    "notes": "Patient allergic to penicillin"
}

# Response
{
    "transaction_id": "uuid",
    "invoice_number": "20250413-0001",
    "total": 5.00,
    "receipt_url": "https://...",
    "whatsapp_sent": true
}
```

## Security Strategy

### 1. Multi-Tenant Data Isolation
- **PostgreSQL RLS**: Database-level enforcement (cannot be bypassed)
- **DRF Permissions**: Application-level validation
- **Tenant Context Middleware**: Automatic shop ID injection
- **QuerySet Filtering**: All queries include `shop=request.user.shop`

### 2. Sensitive Financial Records Protection
- **Encryption at Rest**: Use PostgreSQL pgcrypto for sensitive fields
- **Field-Level Encryption**: Encrypt payment details, card numbers
- **Audit Logging**: All financial operations logged with user/timestamp
- **PCI DSS Compliance**: Never store full card numbers (use Stripe tokens)

### 3. API Security
- **JWT Authentication**: Short-lived tokens with refresh tokens
- **Rate Limiting**: DRF-throttling for POS endpoints
- **CORS Configuration**: Whitelist frontend domain
- **HTTPS Only**: Enforce in production
- **Input Validation**: DRF serializers with strict validation

### 4. DGDA Compliance
- **Audit Logs**: Immutable log of all drug movements
- **Prescription Tracking**: Store prescription images
- **Controlled Substance Tracking**: Special handling for regulated drugs
- **Expiry Monitoring**: Automated alerts for expiring drugs
- **Stock History**: Complete history of all stock adjustments

## Low Stock Prediction (Pandas)

```python
# apps/inventory/services.py
import pandas as pd
from django.utils import timezone
from datetime import timedelta

class InventoryPredictionService:
    @staticmethod
    def predict_stockout(inventory_id, days_ahead=30):
        """
        Predict when inventory will run out based on sales velocity
        
        Algorithm:
        1. Get last 30 days of sales data
        2. Calculate average daily sales
        3. Predict stockout date = current_stock / daily_sales_rate
        4. Apply seasonal adjustments if available
        """
        inventory = ShopInventory.objects.get(id=inventory_id)
        
        # Get sales data for last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        sales_data = TransactionItem.objects.filter(
            inventory=inventory,
            transaction__created_at__gte=thirty_days_ago,
            transaction__status='COMPLETED'
        ).values('transaction__created_at').annotate(
            quantity_sold=Sum('quantity')
        ).order_by('transaction__created_at')
        
        # Convert to DataFrame
        df = pd.DataFrame(list(sales_data))
        
        if df.empty:
            return None
        
        # Calculate daily sales velocity
        df['date'] = pd.to_datetime(df['transaction__created_at']).dt.date
        daily_sales = df.groupby('date')['quantity_sold'].sum()
        avg_daily_sales = daily_sales.mean()
        
        # Predict stockout date
        if avg_daily_sales > 0:
            days_until_stockout = inventory.current_stock / avg_daily_sales
            predicted_stockout = timezone.now().date() + timedelta(days=days_until_stockout)
            
            # Update inventory with prediction
            inventory.predicted_stockout_date = predicted_stockout
            inventory.sales_velocity = avg_daily_sales
            inventory.save()
            
            return {
                'predicted_stockout_date': predicted_stockout,
                'days_until_stockout': int(days_until_stockout),
                'daily_sales_rate': round(avg_daily_sales, 2),
                'current_stock': inventory.current_stock
            }
        
        return None
    
    @staticmethod
    def calculate_expiry_status(expiry_date):
        """Calculate expiry status based on remaining time"""
        today = timezone.now().date()
        days_until_expiry = (expiry_date - today).days
        
        if days_until_expiry > 180:
            return 'GREEN'
        elif days_until_expiry > 30:
            return 'YELLOW'
        else:
            return 'RED'
```

## Performance Optimizations

### 1. Database
- **Indexes**: Strategic indexes on frequently queried fields
- **Partial Indexes**: For filtered queries (e.g., only active items)
- **Connection Pooling**: PgBouncer for high concurrency
- **Read Replicas**: Separate read replicas for analytics

### 2. API
- **Select/Prefetch Related**: Optimize N+1 queries
- **Caching**: Redis cache for frequently accessed data (master catalog)
- **Pagination**: Cursor-based pagination for large datasets
- **Compression**: Gzip compression for API responses

### 3. POS Performance
- **In-Memory Cart**: Store cart in Redis (not database)
- **Bulk Operations**: Bulk create for transaction items
- **Async Notifications**: Celery for WhatsApp/SMS (non-blocking)
- **Optimistic Locking**: Prevent race conditions on stock updates

## Deployment Architecture

```
┌─────────────┐
│   Next.js   │  (Vercel/VPS)
│  Frontend   │
└──────┬──────┘
       │ HTTPS
       ↓
┌─────────────┐
│   Nginx     │  (Reverse Proxy)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Django    │  (Gunicorn)
│   REST API  │
└──────┬──────┘
       │
       ├──────────────┐
       ↓              ↓
┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │    Redis    │
│  (Primary)  │  │   (Cache)   │
└─────────────┘  └─────────────┘
       │
       ↓
┌─────────────┐
│   Celery    │  (Background tasks)
│   Workers   │
└─────────────┘
```

## Next Steps for Implementation

1. **Backend Setup**
   - Configure PostgreSQL with RLS policies
   - Set up Django project with DRF
   - Implement models with migrations
   - Create API viewsets and serializers

2. **Frontend Setup**
   - Initialize Next.js 15 project
   - Install Shadcn UI components
   - Set up API client with React Query
   - Implement authentication flow

3. **Integration**
   - Connect frontend to backend API
   - Implement POS interface with keyboard shortcuts
   - Add real-time features (stock updates)
   - Test multi-tenant isolation

4. **Advanced Features**
   - Implement Celery for async tasks
   - Add WhatsApp/SMS integration
   - Build analytics dashboard
   - Add DGDA compliance features
