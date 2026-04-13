# Smart Pharmacy - SaaS Pharmacy Management System

A comprehensive, multi-tenant pharmacy management system built with Django, featuring role-based access control, inventory management, and a high-speed Point of Sale (POS) interface.

## Features

### Role-Based Access Control (RBAC)
- **SUPER_ADMIN**: Platform-wide management, master catalog CRUD, shop registration
- **SHOP_OWNER**: Inventory management, staff management, financial reporting
- **SHOP_WORKER**: Fast POS interface with keyboard shortcuts

### Key Features
- **Master Catalog**: Global medicine database managed by Super Admin
- **Shop Inventory**: Local inventory with custom pricing, stock, and expiry tracking
- **Point of Sale (POS)**: Keyboard-optimized interface (Ctrl+S, Enter, F10 shortcuts)
- **Transaction Management**: Invoices, payment tracking, customer dues
- **Analytics**: Role-specific dashboards with sales and inventory insights
- **Multi-tenant Data Isolation**: Django ORM filters ensure shops only access their data

## Tech Stack
- **Backend**: Django 5.0.1
- **Database**: SQLite (default)
- **Frontend**: Django Templates + Tailwind CSS
- **Authentication**: Django's built-in auth system with custom User model

## Project Structure

```
SmartPharmacy/
├── smart_pharmacy/          # Main project configuration
│   ├── settings.py          # Django settings with role definitions
│   ├── urls.py              # Main URL configuration
│   └── middleware.py        # RBAC middleware
├── core/                    # Core app with shared functionality
│   ├── middleware.py        # Role-based access decorators
│   └── views.py             # Home and dashboard redirect
├── accounts/                # User authentication and management
│   ├── models.py            # User, Shop, Subscription models
│   ├── forms.py             # Registration and staff creation forms
│   └── views.py             # Login, register, profile views
├── catalog/                 # Master catalog management
│   ├── models.py            # MasterCatalog model
│   └── views.py             # CRUD operations and CSV import
├── inventory/               # Shop-specific inventory
│   ├── models.py            # ShopInventory, StockAdjustment models
│   └── views.py             # Inventory management with shop filtering
├── sales/                   # Transactions and POS
│   ├── models.py            # Transaction, TransactionItem, CustomerDue models
│   └── views.py             # POS interface with keyboard shortcuts
├── dashboard/               # Role-specific dashboards
│   └── views.py             # Analytics widgets for each role
├── templates/               # HTML templates with Tailwind CSS
│   ├── base.html            # Base template
│   ├── accounts/            # Authentication templates
│   ├── dashboard/           # Dashboard templates
│   └── sales/               # POS templates
├── static/                  # Static files
├── media/                   # User uploaded files
├── requirements.txt         # Python dependencies
└── manage.py                # Django management script
```

## Database Schema

### Users & Authentication
- **User**: Custom user model with role (SUPER_ADMIN, SHOP_OWNER, SHOP_WORKER) and shop relationship
- **Shop**: Pharmacy/shop information with license number
- **Subscription**: Subscription plan (Basic, Pro, Enterprise) for each shop

### Catalog & Inventory
- **MasterCatalog**: Global medicines (read-only for shops)
  - Fields: brand_name, type, dosage_form, generic, strength, manufacturer, package_container, package_size
- **ShopInventory**: Junction table linking shops to master catalog
  - Fields: shop, master_medicine, local_price, stock_quantity, expiry_date, batch_number
- **StockAdjustment**: Audit log for stock changes

### Sales & Transactions
- **Customer**: Customer information with shop relationship
- **Transaction**: Invoices with payment method and status
- **TransactionItem**: Individual items in a transaction
- **CustomerDue**: Track customer balances and payments

## Security

### Multi-tenant Data Isolation
- **Django ORM Filters**: All queries filter by `shop=request.user` to ensure data isolation
- **Role-Based Access**: Decorators (`@role_required`) restrict view access by role
- **Shop Assignment**: SHOP_OWNER and SHOP_WORKER must have a shop assigned

### Middleware
- **RoleBasedAccessMiddleware**: Enforces authentication and redirects unauthenticated users
- **role_required()**: View decorator to restrict access by role
- **shop_required()**: Ensures user has a shop assigned before accessing shop-specific features

## Installation

### Prerequisites
- Python 3.10+
- pip

### Setup Steps

1. **Clone the repository**
```bash
cd /home/anik/GitProject/SmartPharmacy
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create a super admin user**
```bash
python manage.py createsuperuser
```
- Set role to SUPER_ADMIN in the database after creation

5. **Import master catalog (optional)**
```bash
python manage.py shell
```
```python
from catalog.views import import_csv
# Use the CSV import feature via admin panel
```

6. **Run the development server**
```bash
python manage.py runserver
```

7. **Access the application**
- Frontend: http://localhost:8000
- Admin Panel: http://localhost:8000/admin

## Usage

### Super Admin Workflow
1. Login as SUPER_ADMIN
2. Register new shops via Dashboard
3. Manage Master Catalog (add/edit medicines)
4. Import medicines from CSV
5. View platform analytics

### Shop Owner Workflow
1. Register as SHOP_OWNER (or assigned by Super Admin)
2. Add medicines from Master Catalog to local inventory
3. Set local pricing and stock quantities
4. Create staff accounts (SHOP_WORKER)
5. View sales reports and analytics

### Shop Worker Workflow
1. Login as SHOP_WORKER
2. Open POS interface
3. Search medicines (Ctrl+S)
4. Add to cart (Enter)
5. Complete sale (F10)
6. Print invoice

## POS Keyboard Shortcuts
- **Ctrl+S**: Open search field
- **Enter**: Add selected medicine to cart
- **F10**: Complete sale and print invoice

## CSV Import Format

The Master Catalog CSV should have the following columns:
```
brand id,brand name,type,slug,dosage form,generic,strength,manufacturer,package container,Package Size
```

Example:
```
4077,A-Cold,allopathic,a-coldsyrup4-mg5-ml,Syrup,Bromhexine Hydrochloride,4 mg/5 ml,ACME Laboratories Ltd.,100 ml bottle: ৳ 40.12,
```

## Development Notes

### Adding New Roles
1. Update `ROLE_CHOICES` in `settings.py`
2. Add role check decorators in `core/middleware.py`
3. Create dashboard view in `dashboard/views.py`

### Customizing POS Interface
- Edit `templates/sales/pos.html` for UI changes
- Modify `sales/views.py` for business logic changes
- Update JavaScript in POS template for keyboard shortcuts

### Database Security
Since this uses SQLite (not PostgreSQL), Row Level Security (RLS) is implemented at the application level:
- All queries filter by `shop=request.user`
- Role decorators prevent unauthorized access
- Never rely on frontend checks for security

## Future Enhancements
- PostgreSQL migration for production RLS
- API endpoints for mobile app integration
- Barcode scanner integration
- Advanced reporting with charts
- Email notifications for low stock
- Subscription billing integration

## License
See LICENSE file for details.