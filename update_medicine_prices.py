#!/usr/bin/env python
"""
Smart Pharmacy - Update Medicine Prices from CSV

This script updates the suggested_price field for existing medicines in the master catalog
using price data from the CSV file.

Usage: python update_medicine_prices.py
"""

import os
import sys
import django
import csv
import re
from decimal import Decimal

# Setup Django
sys.path.append('/home/anik/Personal/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from catalog.models import MasterCatalog

def extract_price(package_container):
    """Extract price from package container field"""
    if not package_container:
        return Decimal('0.00')

    # Try to find price patterns like "৳ 40.12" or "৳40.12"
    # Pattern 1: "৳ X.XX" (Bangladeshi Taka symbol)
    price_pattern = r'৳\s*([\d,]+\.?\d*)'
    matches = re.findall(price_pattern, package_container)

    if matches:
        # Take the first price found (usually the unit price)
        price_str = matches[0].replace(',', '')  # Remove commas
        try:
            return Decimal(price_str)
        except:
            return Decimal('0.00')

    # Pattern 2: Try to find any decimal number that looks like a price
    # This is a fallback for other currency symbols or formats
    decimal_pattern = r':\s*([\d,]+\.?\d*)'
    decimal_matches = re.findall(decimal_pattern, package_container)

    if decimal_matches:
        # Take the first decimal number after a colon
        price_str = decimal_matches[0].replace(',', '')
        try:
            price = Decimal(price_str)
            # Only accept if it looks like a reasonable price (0.01 to 100000)
            if 0.01 <= price <= 100000:
                return price
        except:
            pass

    return Decimal('0.00')

def update_prices():
    print("💰 Starting Medicine Price Update...")
    print("=" * 60)
    
    csv_file_path = 'medicine.csv'
    if not os.path.exists(csv_file_path):
        print(f"❌ Error: {csv_file_path} not found!")
        print("   Please ensure the CSV file is in the project root directory.")
        return
    
    # Counters
    total_rows = 0
    updated = 0
    skipped = 0
    errors = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            
            # Skip header row
            header = next(csv_reader)
            print(f"📋 CSV Headers: {header}")
            print("-" * 60)
            
            for row_num, row in enumerate(csv_reader, start=2):
                total_rows += 1
                
                # Show progress every 1000 rows
                if total_rows % 1000 == 0:
                    print(f"⏳ Processing row {total_rows}...")
                
                # Validate row length
                if len(row) < 10:
                    print(f"⚠️  Row {row_num}: Insufficient data (only {len(row)} columns)")
                    skipped += 1
                    continue

                try:
                    # Extract data
                    brand_id = row[0].strip()
                    brand_name = row[1].strip()
                    package_container = row[8].strip()

                    # Validate brand_id
                    if not brand_id or not brand_id.isdigit():
                        print(f"⚠️  Row {row_num}: Invalid brand_id '{brand_id}', skipping...")
                        skipped += 1
                        continue

                    brand_id = int(brand_id)

                    # Extract price
                    suggested_price = extract_price(package_container)

                    # Find existing medicine
                    try:
                        medicine = MasterCatalog.objects.get(brand_id=brand_id)
                        
                        # Check if price needs updating
                        if medicine.suggested_price != suggested_price:
                            old_price = medicine.suggested_price
                            medicine.suggested_price = suggested_price
                            medicine.save()
                            
                            updated += 1
                            
                            # Show some updates for verification
                            if updated <= 10 or updated % 500 == 0:
                                price_display = f"৳{suggested_price}" if suggested_price > 0 else "No price"
                                print(f"✅ Updated: {medicine.brand_name} | {medicine.brand_id} | ৳{old_price} → {price_display}")
                        else:
                            skipped += 1
                            
                    except MasterCatalog.DoesNotExist:
                        print(f"⚠️  Row {row_num}: Medicine with brand_id {brand_id} not found, skipping...")
                        skipped += 1
                        continue

                except Exception as e:
                    print(f"❌ Error at row {row_num}: {str(e)}")
                    print(f"   Data: {row}")
                    errors += 1
                    continue

    except FileNotFoundError:
        print(f"❌ Error: Could not find {csv_file_path}")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return

    print("=" * 60)
    print("📊 UPDATE SUMMARY")
    print("=" * 60)
    print(f"✅ Total rows processed: {total_rows}")
    print(f"✅ Successfully updated: {updated}")
    print(f"⚠️  Skipped (no change/not found): {skipped}")
    print(f"❌ Errors: {errors}")
    if total_rows > 0:
        print(f"📈 Update rate: {(updated/(total_rows))*100:.1f}%")
    print("=" * 60)

    if updated > 0:
        print("🎉 Price update completed successfully!")
        print(f"💰 {updated} medicines now have updated prices.")
    else:
        print("⚠️  No prices were updated.")

if __name__ == '__main__':
    update_prices()
