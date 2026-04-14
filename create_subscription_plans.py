#!/usr/bin/env python
"""
Create subscription plans for Smart Pharmacy
"""

import os
import sys
import django

sys.path.append('/home/anik/GitProject/SmartPharmacy')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_pharmacy.settings')
django.setup()

from subscriptions.models import SubscriptionPlan


def create_plans():
    print("Creating subscription plans...")
    
    # Basic Plan
    basic, created = SubscriptionPlan.objects.get_or_create(
        slug='basic',
        defaults={
            'name': 'Basic',
            'plan_type': 'basic',
            'price_monthly': 19.99,
            'price_yearly': 199.90,  # ~17% discount
            'description': 'Perfect for small pharmacies getting started',
            'max_users': 2,
            'max_inventory_items': 1000,
            'max_transactions_per_month': 500,
            'analytics_dashboard': False,
            'advanced_reporting': False,
            'api_access': False,
            'priority_support': False,
            'custom_branding': False,
            'multi_location': False,
            'backup_restore': True,
            'sort_order': 1,
        }
    )
    if created:
        print("✅ Created Basic plan")
    
    # Professional Plan (Most Popular)
    professional, created = SubscriptionPlan.objects.get_or_create(
        slug='professional',
        defaults={
            'name': 'Professional',
            'plan_type': 'professional',
            'price_monthly': 49.99,
            'price_yearly': 479.90,  # ~20% discount
            'description': 'Ideal for growing pharmacies with multiple staff',
            'max_users': 5,
            'max_inventory_items': 5000,
            'max_transactions_per_month': 2000,
            'analytics_dashboard': True,
            'advanced_reporting': True,
            'api_access': False,
            'priority_support': True,
            'custom_branding': False,
            'multi_location': False,
            'backup_restore': True,
            'sort_order': 2,
        }
    )
    if created:
        print("✅ Created Professional plan")
    
    # Enterprise Plan
    enterprise, created = SubscriptionPlan.objects.get_or_create(
        slug='enterprise',
        defaults={
            'name': 'Enterprise',
            'plan_type': 'enterprise',
            'price_monthly': 99.99,
            'price_yearly': 959.90,  # ~20% discount
            'description': 'For large pharmacies and chains with advanced needs',
            'max_users': 15,
            'max_inventory_items': 20000,
            'max_transactions_per_month': 10000,
            'analytics_dashboard': True,
            'advanced_reporting': True,
            'api_access': True,
            'priority_support': True,
            'custom_branding': True,
            'multi_location': True,
            'backup_restore': True,
            'sort_order': 3,
        }
    )
    if created:
        print("✅ Created Enterprise plan")
    
    # Premium Plan
    premium, created = SubscriptionPlan.objects.get_or_create(
        slug='premium',
        defaults={
            'name': 'Premium',
            'plan_type': 'premium',
            'price_monthly': 199.99,
            'price_yearly': 1999.90,  # ~17% discount
            'description': 'Ultimate solution for pharmacy networks',
            'max_users': 999999,  # Unlimited
            'max_inventory_items': 999999,  # Unlimited
            'max_transactions_per_month': 999999,  # Unlimited
            'analytics_dashboard': True,
            'advanced_reporting': True,
            'api_access': True,
            'priority_support': True,
            'custom_branding': True,
            'multi_location': True,
            'backup_restore': True,
            'sort_order': 4,
        }
    )
    if created:
        print("✅ Created Premium plan")
    
    print("\n🎉 Subscription plans created successfully!")
    print("\n📋 Available plans:")
    for plan in SubscriptionPlan.objects.all().order_by('sort_order'):
        print(f"  • {plan.name}: ${plan.price_monthly}/month (${plan.price_yearly}/year)")


if __name__ == '__main__':
    create_plans()
