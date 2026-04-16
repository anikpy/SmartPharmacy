#!/usr/bin/env python
"""
Smart Pharmacy - Create Demo Shop Owner and Data

This script creates a demo shop owner, shop, medicines, and sales data for testing.
Run this to set up a complete demo environment.

Usage: python create_demo_data.py
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/anik/Personal/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from decimal import Decimal
from datetime import datetime, timedelta
from users.models import User, Shop
from catalog.models import MasterCatalog
from inventory.models import ShopInventory
from sales.models import Transaction, TransactionItem, Customer

def create_demo_data():
    print("🏥 Creating Demo Shop Owner and Data...")
    print("=" * 60)
    
    # Create Shop
    print("\n📦 Creating Shop...")
    shop, shop_created = Shop.objects.get_or_create(
        license_number='DEMO-SHOP-001',
        defaults={
            'name': 'Demo Pharmacy',
            'address': '123 Demo Street, Dhaka, Bangladesh',
            'phone': '+8801700000000',
            'email': 'demopharmacy@example.com',
            'subscription_tier': 'PRO',
            'is_active': True
        }
    )
    if shop_created:
        print(f"✅ Shop created: {shop.name}")
    else:
        print(f"ℹ️  Shop already exists: {shop.name}")
    
    # Create Shop Owner User
    print("\n👤 Creating Shop Owner User...")
    username = 'demoshop'
    password = 'demo123'
    
    user, user_created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': 'demoshop@example.com',
            'password': make_password(password),
            'first_name': 'Demo',
            'last_name': 'Owner',
            'role': 'SHOP_OWNER',
            'shop': shop,
            'phone': '+8801700000000',
            'is_active': True,
            'is_staff': True
        }
    )
    if user_created:
        print(f"✅ Shop Owner created: {username}")
    else:
        print(f"ℹ️  Shop Owner already exists: {username}")
    
    # Get some medicines from master catalog
    print("\n💊 Adding Medicines to Shop Inventory...")
    medicines_to_add = MasterCatalog.objects.filter(is_active=True)[:10]

    inventory_count = 0
    for medicine in medicines_to_add:
        # Check if already in inventory
        if not ShopInventory.objects.filter(shop=user, master_medicine=medicine).exists():
            ShopInventory.objects.create(
                shop=user,  # User is the shop owner
                master_medicine=medicine,
                local_price=medicine.suggested_price if medicine.suggested_price else Decimal('50.00'),
                stock_quantity=100,
                expiry_date=datetime.now().date() + timedelta(days=365),
                batch_number='N/A',
                low_stock_threshold=10,
                is_active=True
            )
            inventory_count += 1
            print(f"   ✅ Added: {medicine.brand_name} - ৳{medicine.suggested_price if medicine.suggested_price else '50.00'}")

    if inventory_count > 0:
        print(f"✅ Added {inventory_count} medicines to inventory")
    else:
        print(f"ℹ️  Medicines already in inventory")

    # Create some sales
    print("\n💰 Creating Sample Sales...")
    inventory_items = ShopInventory.objects.filter(shop=user, is_active=True)[:5]

    sales_count = 0
    for i in range(3):
        if inventory_items.exists():
            # Create a customer
            customer = Customer.objects.create(
                name=f'Customer {i+1}',
                phone=f'+88017000000{i+1}',
                shop=user  # User is the shop owner
            )

            transaction = Transaction.objects.create(
                shop=user,  # User is the shop owner
                customer=customer,
                subtotal=Decimal('0.00'),
                discount=Decimal('0.00'),
                tax=Decimal('0.00'),
                total=Decimal('0.00'),
                payment_method='cash',
                status='completed',
                created_by=user,
                created_at=datetime.now() - timedelta(days=i)
            )

            # Add items to transaction
            for item in inventory_items[:3]:
                quantity = min(5, item.stock_quantity)
                if quantity > 0:
                    TransactionItem.objects.create(
                        transaction=transaction,
                        inventory=item,
                        medicine_name=item.master_medicine.brand_name,
                        generic_name=item.master_medicine.generic,
                        quantity=quantity,
                        unit_price=item.local_price,
                        total_price=item.local_price * quantity,
                        batch_number=item.batch_number
                    )

            # Recalculate total
            transaction.subtotal = sum(item.total_price for item in transaction.items.all())
            transaction.total = transaction.subtotal - transaction.discount + transaction.tax
            transaction.save()
            sales_count += 1
            print(f"   ✅ Transaction {transaction.invoice_number}: ৳{transaction.total}")

    if sales_count > 0:
        print(f"✅ Created {sales_count} sample transactions")
    else:
        print(f"ℹ️  Transactions already exist")

    print("\n" + "=" * 60)
    print("🎉 Demo Data Creation Complete!")
    print("=" * 60)
    print(f"\n📋 Shop Owner Credentials:")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   Shop: {shop.name}")
    print(f"\n📊 Summary:")
    print(f"   Shop: {shop.name}")
    print(f"   Medicines in Inventory: {ShopInventory.objects.filter(shop=user).count()}")
    print(f"   Transactions Created: {Transaction.objects.filter(shop=user).count()}")
    print("\n💡 You can now login at: http://127.0.0.1:8000/accounts/login/")
    print("=" * 60)

if __name__ == '__main__':
    create_demo_data()
