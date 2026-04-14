#!/usr/bin/env python
"""
Smart Pharmacy - Medicine CSV Import Script

This script imports medicine data from CSV file to SQLite database.
Run this ONCE to populate the master catalog.

Usage: python import_medicines_csv.py

CSV Format Expected:
brand id,brand name,type,slug,dosage form,generic,strength,manufacturer,package container,Package Size
"""

import os
import sys
import django
import csv
import re
from decimal import Decimal

# Setup Django
sys.path.append('/home/anik/GitProject/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from catalog.models import MasterCatalog

def clean_text(text):
    """Clean and normalize text data"""
    if not text or text.strip() == '':
        return ''
    return text.strip().replace('\n', ' ').replace('\r', ' ')

def validate_dosage_form(dosage_form):
    """Validate and map dosage form to our choices"""
    if not dosage_form:
        return 'other'
    
    dosage_form = dosage_form.lower().strip()
    dosage_mapping = {
        'tablet': 'tablet',
        'capsule': 'capsule',
        'syrup': 'syrup',
        'injection': 'injection',
        'powder': 'powder',
        'ointment': 'ointment',
        'cream': 'cream',
        'drops': 'drops',
        'inhaler': 'inhaler',
        'gel': 'ointment',  # Map gel to ointment
        'suspension': 'syrup',  # Map suspension to syrup
        'solution': 'syrup',  # Map solution to syrup
    }
    
    for key, value in dosage_mapping.items():
        if key in dosage_form:
            return value
    
    return 'other'

def validate_medicine_type(med_type):
    """Validate and map medicine type to our choices"""
    if not med_type:
        return 'allopathic'
    
    med_type = med_type.lower().strip()
    if med_type in ['allopathic', 'herbal', 'homeopathic']:
        return med_type
    
    return 'allopathic'  # Default to allopathic

def generate_slug(brand_name, strength):
    """Generate a clean URL slug"""
    if not brand_name:
        return 'unknown-medicine'
    
    text = f"{brand_name}-{strength}" if strength else brand_name
    # Remove special characters and convert to lowercase
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    # Replace spaces and multiple dashes with single dash
    slug = re.sub(r'[\s_-]+', '-', slug)
    # Remove leading/trailing dashes
    slug = slug.strip('-')
    
    return slug[:255]  # Limit to max length

def import_medicines():
    print("🏥 Starting Medicine CSV Import...")
    print("=" * 60)
    
    csv_file_path = 'medicine.csv'
    if not os.path.exists(csv_file_path):
        print(f"❌ Error: {csv_file_path} not found!")
        print("   Please ensure the CSV file is in the project root directory.")
        return
    
    # Counters
    total_rows = 0
    imported = 0
    skipped = 0
    errors = 0
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            
            # Skip header row
            header = next(csv_reader)
            print(f"📋 CSV Headers: {header}")
            print(f"📊 Expected: ['brand id', 'brand name', 'type', 'slug', 'dosage form', 'generic', 'strength', 'manufacturer', 'package container', 'Package Size']")
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
                    # Extract and validate data
                    brand_id = row[0].strip()
                    brand_name = clean_text(row[1])
                    med_type = validate_medicine_type(row[2])
                    slug = clean_text(row[3])
                    dosage_form = validate_dosage_form(row[4])
                    generic = clean_text(row[5])
                    strength = clean_text(row[6])
                    manufacturer = clean_text(row[7])
                    package_container = clean_text(row[8])
                    package_size = clean_text(row[9])

                    # Validate required fields
                    if not brand_name:
                        print(f"⚠️  Row {row_num}: Missing brand name, skipping...")
                        skipped += 1
                        continue

                    if not brand_id or not brand_id.isdigit():
                        print(f"⚠️  Row {row_num}: Invalid brand_id '{brand_id}', skipping...")
                        skipped += 1
                        continue

                    brand_id = int(brand_id)

                    # Check if medicine already exists
                    if MasterCatalog.objects.filter(brand_id=brand_id).exists():
                        # print(f"ℹ️  Row {row_num}: Medicine {brand_name} (ID: {brand_id}) already exists, skipping...")
                        skipped += 1
                        continue

                    # Generate unique slug if empty or if duplicate exists
                    if not slug:
                        slug = generate_slug(brand_name, strength)

                    # Ensure slug is unique
                    original_slug = slug
                    counter = 1
                    while MasterCatalog.objects.filter(slug=slug).exists():
                        slug = f"{original_slug}-{counter}"
                        counter += 1

                    # Create medicine record
                    medicine = MasterCatalog.objects.create(
                        brand_id=brand_id,
                        brand_name=brand_name,
                        type=med_type,
                        slug=slug,
                        dosage_form=dosage_form,
                        generic=generic or brand_name,  # Use brand name if generic is empty
                        strength=strength or 'N/A',
                        manufacturer=manufacturer or 'Unknown',
                        package_container=package_container,
                        package_size=package_size,
                        is_active=True
                    )

                    imported += 1

                    # Show some imported items for verification
                    if imported <= 5 or imported % 500 == 0:
                        print(f"✅ Imported: {medicine.brand_name} | {medicine.generic} | {medicine.strength}")

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
    print("📊 IMPORT SUMMARY")
    print("=" * 60)
    print(f"✅ Total rows processed: {total_rows}")
    print(f"✅ Successfully imported: {imported}")
    print(f"⚠️  Skipped (duplicates/invalid): {skipped}")
    print(f"❌ Errors: {errors}")
    print(f"📈 Success rate: {(imported/(total_rows))*100:.1f}%")
    print("=" * 60)

    if imported > 0:
        print("🎉 Import completed successfully!")
        print(f"💊 {imported} medicines are now available in the master catalog.")
    else:
        print("⚠️  No new medicines were imported.")

if __name__ == '__main__':
    import_medicines()
