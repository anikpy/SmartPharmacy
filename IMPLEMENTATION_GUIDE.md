# Smart Pharmacy SaaS - Implementation Guide

## Project Status: Architecture Migration in Progress

### What Has Been Completed

1. **Architecture Documentation** (`ARCHITECTURE.md`)
   - Complete system architecture
   - Database schema with UUID fields
   - Multi-tenancy strategy (PostgreSQL RLS + Django ORM)
   - API design for POS endpoints
   - Security strategy
   - Low stock prediction algorithm with Pandas

2. **Updated Models** (in existing apps)
   - `users/models.py` - Updated with UUID, DGDA compliance fields
   - `catalog/models.py` - Renamed to MasterMedicine, added DGDA fields
   - `inventory/models.py` - Added expiry tracking, prediction fields
   - `sales/models.py` - Added prescription image, substitute tracking, CRM fields

3. **Inventory Prediction Service**
   - `inventory/services.py` - Pandas-based stockout prediction
   - Expiry tracking logic
   - Low stock alerts

4. **Backend Directory Structure**
   - Created `backend/` directory for new DRF implementation
   - Organized apps: users, catalog, inventory, sales, billing, core

### What Still Needs to Be Done

## Phase 1: Backend Setup (Django REST Framework)

### 1.1 Create Django Project in backend/

```bash
cd backend
django-admin startproject config .
```

### 1.2 Update requirements.txt (backend/requirements.txt)

```
Django==5.0.1
djangorestframework==3.14.0
psycopg2-binary==2.9.9
django-cors-headers==4.3.1
Pillow==10.2.0
python-decouple==3.8
celery==5.3.6
redis==5.0.1
stripe==8.1.0
pandas==2.2.0
numpy==1.26.3
django-filter==23.5
drf-spectacular==0.27.0
```

### 1.3 Configure Settings (backend/config/settings/base.py)

Use the settings from `smart_pharmacy/settings/base.py` that I created earlier.

### 1.4 Create Apps

```bash
cd backend
python manage.py startapp users apps/users
python manage.py startapp catalog apps/catalog
python manage.py startapp inventory apps/inventory
python manage.py startapp sales apps/sales
python manage.py startapp billing apps/billing
python manage.py startapp core apps/core
```

### 1.5 Copy Updated Models

Copy the updated model files from the existing implementation to the new backend:
- `users/models.py` → `backend/apps/users/models.py`
- `catalog/models.py` → `backend/apps/catalog/models.py`
- `inventory/models.py` → `backend/apps/inventory/models.py`
- `sales/models.py` → `backend/apps/sales/models.py`
- `inventory/services.py` → `backend/apps/inventory/services.py`

### 1.6 Create Billing Models (backend/apps/billing/models.py)

```python
import uuid
from django.db import models
from users.models import Shop


class Subscription(models.Model):
    """Shop subscription (Stripe-ready)"""
    PLAN_CHOICES = [
        ('BASIC', 'Basic'),
        ('PRO', 'Pro'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    stripe_customer_id = models.CharField(max_length=100, unique=True)
    stripe_subscription_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20)  # active, past_due, cancelled
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Invoice(models.Model):
    """Billing invoices"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='invoices')
    stripe_invoice_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)  # draft, open, paid, void
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Phase 2: DRF Serializers & ViewSets

### 2.1 Create Serializers

**backend/apps/users/serializers.py**
```python
from rest_framework import serializers
from .models import User, Shop

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'shop', 'phone', 'avatar']
        read_only_fields = ['id']
```

**backend/apps/inventory/serializers.py**
```python
from rest_framework import serializers
from .models import ShopInventory
from catalog.models import MasterMedicine

class ShopInventorySerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='master_medicine.brand_name', read_only=True)
    generic_name = serializers.CharField(source='master_medicine.generic_name', read_only=True)
    
    class Meta:
        model = ShopInventory
        fields = '__all__'
```

**backend/apps/sales/serializers.py**
```python
from rest_framework import serializers
from .models import Transaction, TransactionItem, Customer

class TransactionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionItem
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    items = TransactionItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'
```

### 2.2 Create ViewSets

**backend/apps/inventory/views.py**
```python
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ShopInventory
from .serializers import ShopInventorySerializer
from .services import InventoryPredictionService
from core.permissions import IsShopOwnerOrWorker
from django.conf import settings

class ShopInventoryViewSet(viewsets.ModelViewSet):
    serializer_class = ShopInventorySerializer
    permission_classes = [IsShopOwnerOrWorker]
    
    def get_queryset(self):
        return ShopInventory.objects.filter(shop=self.request.user.shop)
    
    @action(detail=True, methods=['get'])
    def predict_stockout(self, request, pk=None):
        """Predict when this inventory item will run out"""
        result = InventoryPredictionService.predict_stockout(pk)
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        """Get all low stock items for the shop"""
        alerts = InventoryPredictionService.get_low_stock_alerts(
            request.user.shop.id
        )
        return Response(alerts)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get items expiring within 30 days"""
        expiring = InventoryPredictionService.get_expiring_soon(
            request.user.shop.id
        )
        return Response(expiring)
```

**backend/apps/sales/views.py**
```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Transaction, TransactionItem, Customer
from .serializers import TransactionSerializer
from inventory.models import ShopInventory
from core.permissions import IsShopOwnerOrWorker
from core.exceptions import InsufficientStockError

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsShopOwnerOrWorker]
    
    def get_queryset(self):
        return Transaction.objects.filter(shop=self.request.user.shop)
    
    def create(self, request, *args, **kwargs):
        """Create transaction with stock deduction"""
        with transaction.atomic():
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Deduct stock
            for item_data in request.data.get('items', []):
                inventory = ShopInventory.objects.get(
                    id=item_data['inventory_id'],
                    shop=request.user.shop
                )
                if inventory.current_stock < item_data['quantity']:
                    raise InsufficientStockError(
                        f"Insufficient stock for {inventory.master_medicine.brand_name}"
                    )
                inventory.current_stock -= item_data['quantity']
                inventory.save()
            
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
```

### 2.3 Create POS Search View

**backend/apps/sales/views.py** (add to file)
```python
class POSMedicineSearchView(APIView):
    permission_classes = [IsShopOwnerOrWorker]
    
    def get(self, request):
        """Search medicines for POS"""
        query = request.query_params.get('q', '')
        medicines = ShopInventory.objects.filter(
            shop=request.user.shop,
            master_medicine__brand_name__icontains=query,
            is_active=True
        ).select_related('master_medicine')[:10]
        
        results = []
        for item in medicines:
            results.append({
                'id': str(item.id),
                'medicine_name': item.master_medicine.brand_name,
                'generic_name': item.master_medicine.generic_name,
                'strength': item.master_medicine.strength,
                'stock': item.current_stock,
                'price': float(item.selling_price),
                'expiry_date': item.expiry_date.isoformat(),
                'expiry_status': item.expiry_status,
                'batch_number': item.batch_number
            })
        
        return Response({'results': results})
```

### 2.4 Configure URLs

**backend/config/urls.py**
```python
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.inventory.views import ShopInventoryViewSet
from apps.sales.views import TransactionViewSet, POSMedicineSearchView

router = DefaultRouter()
router.register(r'inventory', ShopInventoryViewSet, basename='inventory')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/pos/search/', POSMedicineSearchView.as_view(), name='pos-search'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
]
```

## Phase 3: PostgreSQL Setup

### 3.1 Enable Row Level Security

Create migration file or execute SQL:

```sql
-- Enable RLS on tenant-scoped tables
ALTER TABLE shop_inventory ENABLE ROW LEVEL SECURITY;

-- Create policy for shop isolation
CREATE POLICY shop_isolation ON shop_inventory
    USING (shop_id = current_setting('app.current_shop_id')::UUID);

-- Similar policies for transactions, customers, etc.
```

### 3.2 Configure Database

Update `backend/config/settings/base.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'smart_pharmacy'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

## Phase 4: Frontend Setup (Next.js 15)

### 4.1 Create Next.js Project

```bash
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npx shadcn-ui@latest init
```

### 4.2 Install Dependencies

```bash
npm install @tanstack/react-query axios zustand react-hook-form zod
npm install @radix-ui/react-icons lucide-react
```

### 4.3 Create API Client

**frontend/lib/api.ts**
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export default api;
```

### 4.4 Create POS Component

**frontend/components/pos/POSInterface.tsx**
```typescript
'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';

export default function POSInterface() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [cart, setCart] = useState([]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        document.getElementById('search-input')?.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const searchMedicines = async (query: string) => {
    const response = await api.get('/pos/search/', { params: { q: query } });
    setResults(response.data.results);
  };

  return (
    <div className="p-6">
      <input
        id="search-input"
        type="text"
        placeholder="Search medicines (Ctrl+S)"
        className="w-full p-3 border rounded-lg"
        value={searchQuery}
        onChange={(e) => {
          setSearchQuery(e.target.value);
          searchMedicines(e.target.value);
        }}
      />
      {/* Results and cart UI */}
    </div>
  );
}
```

## Phase 5: Deployment

### 5.1 Docker Setup

**docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: smart_pharmacy
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
      - media_volume:/app/media
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  media_volume:
```

## Phase 6: Advanced Features

### 6.1 Celery Tasks for Notifications

**backend/apps/notifications/tasks.py**
```python
from celery import shared_task
from .services import WhatsAppService, SMSService

@shared_task
def send_receipt(transaction_id):
    """Send receipt via WhatsApp/SMS"""
    transaction = Transaction.objects.get(id=transaction_id)
    if transaction.customer:
        WhatsAppService.send_receipt(transaction)
```

### 6.2 DGDA Compliance Logging

**backend/apps/compliance/models.py**
```python
from django.db import models

class AuditLog(models.Model):
    """Immutable audit log for DGDA compliance"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    table_name = models.CharField(max_length=100)
    record_id = models.UUIDField()
    action = models.CharField(max_length=20)  # CREATE, UPDATE, DELETE
    old_values = models.JSONField(null=True)
    new_values = models.JSONField(null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
        ]
```

## Next Steps

1. **Choose your approach**:
   - Continue with the backend/ directory structure (recommended)
   - Or overwrite existing files with DRF versions

2. **Install PostgreSQL** if not already installed

3. **Set up environment variables** (.env file)

4. **Run migrations**:
   ```bash
   cd backend
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create super admin and test data**

6. **Start building the Next.js frontend**

## Files Created/Modified

- ✅ ARCHITECTURE.md - Complete architecture documentation
- ✅ backend/ directory structure
- ✅ Updated models in existing apps (users, catalog, inventory, sales)
- ✅ inventory/services.py - Prediction service with Pandas
- ✅ smart_pharmacy/settings/base.py - DRF configuration
- ✅ requirements.txt - Updated dependencies

## Key Decisions Made

1. **UUID Primary Keys**: For better security and distributed systems
2. **PostgreSQL RLS**: Database-level multi-tenant isolation
3. **Pandas for Predictions**: Accurate stockout predictions based on sales velocity
4. **Separate Backend/Frontend**: Clean separation for scalability
5. **DGDA Compliance**: Built-in regulatory compliance features

## Questions?

1. Should I continue building out the DRF backend in the `backend/` directory?
2. Or should I overwrite the existing files?
3. Do you want me to focus on a specific part (e.g., POS API, frontend, etc.)?
