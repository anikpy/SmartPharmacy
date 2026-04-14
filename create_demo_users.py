#!/usr/bin/env python
"""
Create demo users for Smart Pharmacy application
Run this script to set up demo accounts for testing
"""

import os
import sys
import django

# Add the project root to Python path
sys.path.append('/home/anik/GitProject/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from users.models import User, Shop
from django.conf import settings

def create_demo_users():
    print("Creating demo users for Smart Pharmacy...")
    
    # Create a demo shop
    shop, created = Shop.objects.get_or_create(
        license_number='DEMO001',
        defaults={
            'name': 'Demo Pharmacy',
            'address': '123 Main Street, Dhaka, Bangladesh',
            'phone': '+880123456789',
            'email': 'demo@smartpharmacy.com',
            'dgda_license': 'DGDA-DEMO-001',
            'subscription_tier': 'PRO',
        }
    )
    
    if created:
        print(f"✅ Created demo shop: {shop.name}")
    else:
        print(f"ℹ️  Demo shop already exists: {shop.name}")
    
    # Create Super Admin
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@smartpharmacy.com',
            first_name='System',
            last_name='Administrator',
            role=settings.ROLE_SUPER_ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        print(f"✅ Created Super Admin: {admin_user.username}")
    else:
        print("ℹ️  Super Admin already exists")
    
    # Create Shop Owner
    if not User.objects.filter(username='owner1').exists():
        owner_user = User.objects.create_user(
            username='owner1',
            password='pass123',
            email='owner@demopharmacy.com',
            first_name='John',
            last_name='Doe',
            role=settings.ROLE_SHOP_OWNER,
            shop=shop,
        )
        print(f"✅ Created Shop Owner: {owner_user.username}")
    else:
        print("ℹ️  Shop Owner already exists")
    
    # Create Shop Worker
    if not User.objects.filter(username='worker1').exists():
        worker_user = User.objects.create_user(
            username='worker1',
            password='pass123',
            email='worker@demopharmacy.com',
            first_name='Jane',
            last_name='Smith',
            role=settings.ROLE_SHOP_WORKER,
            shop=shop,
        )
        print(f"✅ Created Shop Worker: {worker_user.username}")
    else:
        print("ℹ️  Shop Worker already exists")
    
    print("\n🎉 Demo users setup complete!")
    print("\n📋 Login Credentials:")
    print("Super Admin: admin / admin123")
    print("Shop Owner:  owner1 / pass123")
    print("Shop Worker: worker1 / pass123")
    print("\n🚀 Start the server with: python manage.py runserver")
    print("🌐 Access at: http://localhost:8000")

if __name__ == '__main__':
    create_demo_users()
