#!/usr/bin/env python
"""
Check current database schema vs model definitions
"""

import os
import sys
import django

sys.path.append('/home/anik/GitProject/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from django.db import connection
from sales.models import Transaction
from inventory.models import ShopInventory

def check_table_schema():
    """Check current database table structure"""
    cursor = connection.cursor()
    
    print("🔍 CHECKING DATABASE SCHEMA")
    print("=" * 60)
    
    # Check Transaction table
    print("\n📊 TRANSACTION TABLE SCHEMA:")
    try:
        cursor.execute("PRAGMA table_info(sales_transaction);")
        transaction_columns = cursor.fetchall()
        
        print("Current columns in database:")
        for col in transaction_columns:
            print(f"  - {col[1]} ({col[2]})")
            
        # Check what fields the model expects
        print("\nModel expects these fields:")
        model_fields = [f.column for f in Transaction._meta.get_fields() if hasattr(f, 'column')]
        for field in Transaction._meta.get_fields():
            if hasattr(field, 'column'):
                print(f"  - {field.column} ({field.name})")
    except Exception as e:
        print(f"❌ Error checking transaction table: {e}")
    
    # Check ShopInventory table  
    print("\n📦 INVENTORY TABLE SCHEMA:")
    try:
        cursor.execute("PRAGMA table_info(shop_inventory);")
        inventory_columns = cursor.fetchall()
        
        print("Current columns in database:")
        for col in inventory_columns:
            print(f"  - {col[1]} ({col[2]})")
            
        print("\nModel expects these fields:")
        for field in ShopInventory._meta.get_fields():
            if hasattr(field, 'column'):
                print(f"  - {field.column} ({field.name})")
    except Exception as e:
        print(f"❌ Error checking inventory table: {e}")

def check_pending_migrations():
    """Check if there are pending migrations"""
    print("\n🔄 CHECKING PENDING MIGRATIONS:")
    
    from django.core.management import execute_from_command_line
    import sys
    from io import StringIO
    
    # Capture the output
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        execute_from_command_line(['manage.py', 'showmigrations', '--plan'])
    except SystemExit:
        pass
    
    sys.stdout = old_stdout
    output = captured_output.getvalue()
    
    if '[ ]' in output:
        print("❌ PENDING MIGRATIONS FOUND!")
        print(output)
    else:
        print("✅ All migrations applied")

if __name__ == '__main__':
    check_table_schema()
    check_pending_migrations()
    
    print("\n" + "=" * 60)
    print("💡 RECOMMENDATION:")
    print("1. Run: python manage.py makemigrations")  
    print("2. Run: python manage.py migrate")
    print("3. This will update database to match new model structure")
