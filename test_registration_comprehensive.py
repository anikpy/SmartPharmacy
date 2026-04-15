#!/usr/bin/env python
"""
Comprehensive Registration Form Test
Tests both form validation and template rendering
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/anik/Personal/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from users.forms import UserRegistrationForm
from users.models import User, Shop
from django.conf import settings

def test_form_validation():
    print("=" * 70)
    print("🧪 REGISTRATION FORM VALIDATION TESTS")
    print("=" * 70)

    # Test 1: Minimal valid registration (without optional fields)
    print("\n✓ Test 1: Minimal Registration (No first_name, last_name, phone)")
    print("-" * 70)
    data1 = {
        'username': 'minimaluser',
        'email': 'minimal@example.com',
        'role': 'SHOP_OWNER',
        'password1': 'SecurePass@123',
        'password2': 'SecurePass@123',
    }
    form1 = UserRegistrationForm(data1)
    if form1.is_valid():
        print("✅ PASS - Form accepted without optional fields")
    else:
        print("❌ FAIL - Form errors:")
        for field, errors in form1.errors.items():
            print(f"   {field}: {errors}")
        return False

    # Test 2: Full registration with all fields
    print("\n✓ Test 2: Full Registration (All fields populated)")
    print("-" * 70)
    data2 = {
        'username': 'fulluser',
        'email': 'full@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone': '9876543210',
        'role': 'SHOP_OWNER',
        'password1': 'SecurePass@123',
        'password2': 'SecurePass@123',
    }
    form2 = UserRegistrationForm(data2)
    if form2.is_valid():
        print("✅ PASS - Form accepted with all fields")
        print(f"   Username: {form2.cleaned_data['username']}")
        print(f"   Email: {form2.cleaned_data['email']}")
        print(f"   First Name: {form2.cleaned_data.get('first_name', 'N/A')}")
        print(f"   Last Name: {form2.cleaned_data.get('last_name', 'N/A')}")
        print(f"   Role: {form2.cleaned_data['role']}")
    else:
        print("❌ FAIL - Form errors:")
        for field, errors in form2.errors.items():
            print(f"   {field}: {errors}")
        return False

    # Test 3: Password mismatch
    print("\n✓ Test 3: Password Mismatch Validation")
    print("-" * 70)
    data3 = {
        'username': 'passuser',
        'email': 'pass@example.com',
        'role': 'SHOP_OWNER',
        'password1': 'SecurePass@123',
        'password2': 'DifferentPass@456',
    }
    form3 = UserRegistrationForm(data3)
    if not form3.is_valid() and 'password2' in form3.errors:
        print("✅ PASS - Password mismatch correctly detected")
    else:
        print("❌ FAIL - Password validation not working")
        return False

    # Test 4: Missing required field (username)
    print("\n✓ Test 4: Missing Required Field (Username)")
    print("-" * 70)
    data4 = {
        'email': 'nouser@example.com',
        'role': 'SHOP_OWNER',
        'password1': 'SecurePass@123',
        'password2': 'SecurePass@123',
    }
    form4 = UserRegistrationForm(data4)
    if not form4.is_valid() and 'username' in form4.errors:
        print("✅ PASS - Missing username correctly detected")
    else:
        print("❌ FAIL - Required field validation not working")
        return False

    # Test 5: Invalid email format
    print("\n✓ Test 5: Invalid Email Format")
    print("-" * 70)
    data5 = {
        'username': 'emailuser',
        'email': 'not-an-email',
        'role': 'SHOP_OWNER',
        'password1': 'SecurePass@123',
        'password2': 'SecurePass@123',
    }
    form5 = UserRegistrationForm(data5)
    if not form5.is_valid() and 'email' in form5.errors:
        print("✅ PASS - Invalid email correctly detected")
    else:
        print("❌ FAIL - Email validation not working")
        return False

    # Test 6: Role field validation
    print("\n✓ Test 6: Valid Role Selection")
    print("-" * 70)
    for role_code, role_name in settings.ROLE_CHOICES:
        data6 = {
            'username': f'roleuser_{role_code}',
            'email': f'role{role_code}@example.com',
            'role': role_code,
            'password1': 'SecurePass@123',
            'password2': 'SecurePass@123',
        }
        form6 = UserRegistrationForm(data6)
        if form6.is_valid():
            print(f"✅ Role '{role_name}' is valid")
        else:
            print(f"❌ Role '{role_name}' validation failed")
            return False

    print("\n" + "=" * 70)
    print("✅ ALL FORM VALIDATION TESTS PASSED!")
    print("=" * 70)
    return True


def test_field_requirements():
    print("\n" + "=" * 70)
    print("🔍 FORM FIELD REQUIREMENTS CHECK")
    print("=" * 70)

    form = UserRegistrationForm()

    required_fields = ['username', 'email', 'password1', 'password2', 'role']
    optional_fields = ['first_name', 'last_name', 'phone']

    print("\n📋 Required Fields:")
    for field_name in required_fields:
        if field_name in form.fields:
            is_required = form.fields[field_name].required
            status = "✅ Required" if is_required else "❌ NOT Required"
            print(f"   {field_name}: {status}")
        else:
            print(f"   {field_name}: ❌ NOT FOUND")

    print("\n📋 Optional Fields:")
    for field_name in optional_fields:
        if field_name in form.fields:
            is_required = form.fields[field_name].required
            status = "✅ Optional" if not is_required else "❌ REQUIRED"
            print(f"   {field_name}: {status}")
        else:
            print(f"   {field_name}: ❌ NOT FOUND")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    success = test_form_validation()
    if success:
        test_field_requirements()
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

