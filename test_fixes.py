#!/usr/bin/env python
"""
Test the fixes for User-Shop relationship and logout functionality
"""

import os
import sys
import django

sys.path.append('/home/anik/GitProject/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from users.models import User, Shop

def test_user_shop_relationship():
    """Test that user-shop relationships are working correctly"""
    print("🧪 Testing User-Shop Relationships...")
    
    # Get a shop owner user
    owner = User.objects.filter(role='SHOP_OWNER').first()
    
    if owner:
        print(f"✅ Found shop owner: {owner.username}")
        
        if owner.shop:
            print(f"✅ Shop owner has shop: {owner.shop.name}")
            
            # Test querying inventory
            try:
                from inventory.models import ShopInventory
                inventory_count = ShopInventory.objects.filter(shop=owner.shop).count()
                print(f"✅ Inventory query works: {inventory_count} items found")
            except Exception as e:
                print(f"❌ Inventory query failed: {e}")
            
            # Test querying transactions
            try:
                from sales.models import Transaction
                transaction_count = Transaction.objects.filter(shop=owner.shop).count()
                print(f"✅ Transaction query works: {transaction_count} transactions found")
            except Exception as e:
                print(f"❌ Transaction query failed: {e}")
        else:
            print("⚠️  Shop owner has no shop assigned")
    else:
        print("❌ No shop owner found")

def test_logout_urls():
    """Test that logout URLs are configured correctly"""
    print("\n🧪 Testing Logout URLs...")
    
    from django.urls import reverse
    
    try:
        logout_url = reverse('users:logout')
        print(f"✅ Logout URL resolves: {logout_url}")
    except Exception as e:
        print(f"❌ Logout URL error: {e}")

def test_dashboard_fields():
    """Test that dashboard views can access the correct model fields"""
    print("\n🧪 Testing Dashboard Model Fields...")
    
    try:
        from inventory.models import ShopInventory
        # Test the field names we're using in dashboard
        fields = ShopInventory._meta.get_fields()
        field_names = [f.name for f in fields]
        
        required_fields = ['shop', 'medicine', 'quantity', 'purchase_price', 'selling_price', 'low_stock_threshold']
        
        for field in required_fields:
            if field in field_names:
                print(f"✅ Field exists: {field}")
            else:
                print(f"❌ Missing field: {field}")
                
    except Exception as e:
        print(f"❌ Model field test failed: {e}")

if __name__ == '__main__':
    print("🔧 TESTING SMART PHARMACY FIXES")
    print("=" * 50)
    
    test_user_shop_relationship()
    test_logout_urls()
    test_dashboard_fields()
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")
    print("\n💡 If all tests pass, try:")
    print("1. Login as owner1 / pass123")
    print("2. Visit /dashboard/shop-owner/")
    print("3. Test logout functionality")
