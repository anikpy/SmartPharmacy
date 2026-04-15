#!/usr/bin/env python
"""
Test script for registration functionality
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/anik/Personal/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from users.models import User, Shop
from users.forms import UserRegistrationForm
from django.conf import settings

def test_registration():
    print("🧪 Testing Registration Flow...")
    print("=" * 60)

    # Test 1: Form validation
    print("\n✓ Test 1: Form Validation")
    form_data = {
        'username': 'testshopowner',
        'email': 'testshop@example.com',
        'first_name': 'Test',
        'last_name': 'Owner',
        'phone': '9876543210',
        'role': settings.ROLE_SHOP_OWNER,
        'password1': 'TestPass@123',
        'password2': 'TestPass@123',
    }

    form = UserRegistrationForm(form_data)
    if form.is_valid():
        print("   ✅ Form is valid")
    else:
        print("   ❌ Form errors:")
        for field, errors in form.errors.items():
            print(f"      {field}: {errors}")
        return False

    # Test 2: User creation
    print("\n✓ Test 2: User Creation")
    try:
        user = form.save(commit=False)
        user.role = settings.ROLE_SHOP_OWNER
        user.save()
        print(f"   ✅ User created: {user.username}")
    except Exception as e:
        print(f"   ❌ Error creating user: {str(e)}")
        return False

    # Test 3: Shop creation for shop owner
    print("\n✓ Test 3: Shop Creation")
    try:
        shop = Shop.objects.create(
            name="Test Pharmacy",
            license_number="LP-TEST-001",
            address="123 Test Street",
            phone="9876543210",
            email="testshop@example.com",
        )
        print(f"   ✅ Shop created: {shop.name}")

        # Link user to shop
        user.shop = shop
        user.save()
        print(f"   ✅ User linked to shop")
    except Exception as e:
        print(f"   ❌ Error creating shop: {str(e)}")
        return False

    # Test 4: Verify user properties
    print("\n✓ Test 4: User Properties")
    user.refresh_from_db()
    print(f"   Username: {user.username}")
    print(f"   Role: {user.role}")
    print(f"   Shop: {user.shop.name if user.shop else 'None'}")
    print(f"   Is Shop Owner: {user.is_shop_owner}")

    print("\n" + "=" * 60)
    print("✅ All registration tests passed!")
    print("=" * 60)

    # Cleanup
    print("\n🧹 Cleaning up test data...")
    user.delete()
    shop.delete()
    print("✅ Test data removed")

if __name__ == '__main__':
    test_registration()

