#!/usr/bin/env python
"""
Smart Pharmacy - Create Super Admin Script

This script creates the super admin user with predefined credentials.
Run this ONCE to set up the super admin account.

Super Admin Credentials:
- Username: Anik
- Email: anik@gmail.com
- Password: Anik@320
- Role: SUPER_ADMIN

Usage: python create_super_admin.py
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/anik/Personal/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from users.models import User

def create_super_admin():
    print("👑 Creating Super Admin Account...")
    print("=" * 60)

    # Super admin credentials
    username = 'Anik'
    email = 'anik@gmail.com'
    password = 'Anik@320'
    first_name = 'Anik'
    role = 'SUPER_ADMIN'

    # Check if super admin already exists
    if User.objects.filter(username=username).exists():
        print(f"ℹ️  Super admin '{username}' already exists.")
        print("   Skipping creation to avoid duplicates.")
        return

    try:
        # Create super admin user
        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            role=role,
            is_superuser=True,
            is_staff=True,
            is_active=True
        )

        # Set password
        user.set_password(password)
        user.save()

        print("✅ Super Admin created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Role: {role}")
        print("   Password has been set.")
        print("=" * 60)
        print("🔐 Super Admin account is ready for login.")

    except Exception as e:
        print(f"❌ Error creating super admin: {str(e)}")
        return

if __name__ == '__main__':
    create_super_admin()
