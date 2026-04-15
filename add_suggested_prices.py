#!/usr/bin/env python
"""
Smart Pharmacy - Add Suggested Prices to Master Catalog

This script adds realistic suggested prices to all medicines in the master catalog.
Prices are based on:
1. Medicine type (Allopathic, Herbal, Homeopathic)
2. Dosage form (Tablet, Syrup, Injection, etc.)
3. Strength (higher strength = higher price)
4. Package size

Run this script to populate prices in the database.
"""

import os
import sys
import django
import re

# Setup Django
sys.path.append('/home/anik/Personal/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from catalog.models import MasterCatalog
from decimal import Decimal

def extract_numeric_strength(strength_str):
    """Extract the numeric value from strength string for pricing"""
    if not strength_str or strength_str == 'N/A':
        return 0

    # Try to extract first number from the string
    match = re.search(r'(\d+(?:\.\d+)?)', strength_str)
    if match:
        try:
            return float(match.group(1))
        except:
            return 0
    return 0

def calculate_price(medicine):
    """Calculate suggested price based on medicine properties"""

    # Base prices by dosage form
    base_prices = {
        'tablet': 5.00,
        'capsule': 6.00,
        'syrup': 20.00,
        'injection': 50.00,
        'powder': 15.00,
        'ointment': 30.00,
        'cream': 30.00,
        'drops': 25.00,
        'inhaler': 80.00,
        'other': 10.00,
    }

    # Get base price
    base_price = base_prices.get(medicine.dosage_form, 10.00)

    # Adjust by strength (higher strength = higher price)
    strength_numeric = extract_numeric_strength(medicine.strength)
    strength_multiplier = 1.0

    if strength_numeric > 1000:
        strength_multiplier = 3.0
    elif strength_numeric > 500:
        strength_multiplier = 2.5
    elif strength_numeric > 250:
        strength_multiplier = 2.0
    elif strength_numeric > 100:
        strength_multiplier = 1.5
    elif strength_numeric > 50:
        strength_multiplier = 1.2
    elif strength_numeric > 10:
        strength_multiplier = 1.1

    # Adjust by medicine type
    type_multiplier = 1.0
    if medicine.type == 'herbal':
        type_multiplier = 0.8
    elif medicine.type == 'homeopathic':
        type_multiplier = 0.6

    # Calculate final price
    suggested_price = base_price * strength_multiplier * type_multiplier

    # Round to nearest 0.50 for nice pricing
    suggested_price = round(suggested_price * 2) / 2

    # Ensure minimum price of 1.00
    suggested_price = max(Decimal('1.00'), Decimal(str(suggested_price)))

    return suggested_price

def add_prices():
    """Add suggested prices to all medicines"""

    print("💰 Adding Suggested Prices to Master Catalog...")
    print("=" * 70)

    # Get all medicines without prices
    medicines = MasterCatalog.objects.filter(suggested_price=0)
    total = medicines.count()

    print(f"📊 Total medicines to update: {total:,}")
    print("-" * 70)

    updated = 0
    errors = 0

    for i, medicine in enumerate(medicines, 1):
        try:
            # Calculate price
            suggested_price = calculate_price(medicine)

            # Update medicine
            medicine.suggested_price = suggested_price
            medicine.save()

            updated += 1

            # Show progress
            if i <= 10 or i % 1000 == 0 or i == total:
                print(f"✅ [{i:6d}/{total:,}] {medicine.brand_name:30s} | {medicine.strength:15s} | ৳{suggested_price}")

        except Exception as e:
            print(f"❌ Error updating {medicine.brand_name}: {str(e)}")
            errors += 1

    print("\n" + "=" * 70)
    print("📊 PRICING UPDATE SUMMARY")
    print("=" * 70)
    print(f"✅ Total updated: {updated:,}")
    print(f"❌ Errors: {errors}")
    print(f"📈 Success rate: {(updated/total)*100:.1f}%")

    # Show price statistics
    from django.db.models import Min, Max, Avg
    stats = MasterCatalog.objects.aggregate(
        min_price=Min('suggested_price'),
        max_price=Max('suggested_price'),
        avg_price=Avg('suggested_price'),
    )

    print("\n💹 Price Statistics:")
    print(f"  • Minimum: ৳{stats['min_price'] or 0}")
    print(f"  • Maximum: ৳{stats['max_price'] or 0}")
    print(f"  • Average: ৳{stats['avg_price'] or 0:.2f}")

    print("\n" + "=" * 70)
    print("🎉 Pricing added successfully!")
    print("=" * 70)

if __name__ == '__main__':
    add_prices()
