from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, Subscription, Payment
from users.models import Shop


def pricing(request):
    """
    Public pricing page for potential customers
    """
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'price_monthly')
    
    # Calculate features comparison
    features_matrix = []
    if plans:
        all_features = [
            {'key': 'max_users', 'name': 'Team Members', 'type': 'number'},
            {'key': 'max_inventory_items', 'name': 'Inventory Items', 'type': 'number'},
            {'key': 'max_transactions_per_month', 'name': 'Monthly Transactions', 'type': 'number'},
            {'key': 'analytics_dashboard', 'name': 'Analytics Dashboard', 'type': 'boolean'},
            {'key': 'advanced_reporting', 'name': 'Advanced Reporting', 'type': 'boolean'},
            {'key': 'api_access', 'name': 'API Access', 'type': 'boolean'},
            {'key': 'priority_support', 'name': '24/7 Priority Support', 'type': 'boolean'},
            {'key': 'custom_branding', 'name': 'Custom Branding', 'type': 'boolean'},
            {'key': 'multi_location', 'name': 'Multi-Location', 'type': 'boolean'},
            {'key': 'backup_restore', 'name': 'Backup & Restore', 'type': 'boolean'},
        ]
        
        for feature in all_features:
            feature_row = {
                'name': feature['name'],
                'type': feature['type'],
                'plans': []
            }
            
            for plan in plans:
                value = getattr(plan, feature['key'])
                if feature['type'] == 'number':
                    if value >= 999999:
                        display_value = 'Unlimited'
                    else:
                        display_value = f"{value:,}"
                else:
                    display_value = value
                
                feature_row['plans'].append({
                    'value': value,
                    'display': display_value
                })
            
            features_matrix.append(feature_row)
    
    context = {
        'plans': plans,
        'features_matrix': features_matrix,
        'user_is_authenticated': request.user.is_authenticated,
    }
    
    return render(request, 'subscriptions/pricing.html', context)


@login_required
def choose_plan(request, plan_slug):
    """
    Allow authenticated users to choose a subscription plan
    """
    plan = get_object_or_404(SubscriptionPlan, slug=plan_slug, is_active=True)
    
    if request.method == 'POST':
        billing_cycle = request.POST.get('billing_cycle', 'monthly')
        
        # Check if user has a shop
        if not hasattr(request.user, 'shop') or not request.user.shop:
            messages.error(request, 'You need to register a pharmacy first before subscribing.')
            return redirect('users:register_shop')
        
        # Calculate subscription details
        if billing_cycle == 'yearly':
            amount = plan.price_yearly
            end_date = timezone.now() + timedelta(days=365)
        else:
            amount = plan.price_monthly
            end_date = timezone.now() + timedelta(days=30)
        
        # Create or update subscription
        subscription, created = Subscription.objects.get_or_create(
            shop=request.user.shop,
            defaults={
                'plan': plan,
                'status': 'pending',
                'billing_cycle': billing_cycle,
                'start_date': timezone.now(),
                'end_date': end_date,
                'current_amount': amount,
                'auto_renew': True,
            }
        )
        
        if not created:
            # Update existing subscription
            subscription.plan = plan
            subscription.billing_cycle = billing_cycle
            subscription.current_amount = amount
            subscription.end_date = end_date
            subscription.status = 'pending'
            subscription.save()
        
        # Create payment record
        payment = Payment.objects.create(
            subscription=subscription,
            amount=amount,
            payment_method='pending',
            status='pending'
        )
        
        messages.success(request, f'Subscription plan selected! Please complete payment to activate.')
        return redirect('subscriptions:payment', payment_id=payment.id)
    
    context = {
        'plan': plan,
        'user_shop': getattr(request.user, 'shop', None),
    }
    
    return render(request, 'subscriptions/choose_plan.html', context)


@login_required
def payment(request, payment_id):
    """
    Payment processing page
    """
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Ensure user owns this payment
    if payment.subscription.shop != request.user.shop:
        messages.error(request, 'Access denied.')
        return redirect('subscriptions:my_subscription')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        
        # For demo purposes, we'll simulate payment success
        # In production, integrate with Stripe, PayPal, bKash, etc.
        
        if payment_method in ['stripe', 'paypal', 'bkash', 'nagad']:
            # Simulate successful payment
            payment.payment_method = payment_method
            payment.status = 'completed'
            payment.transaction_id = f'DEMO_{payment_method.upper()}_{payment.id}'
            payment.save()
            
            # Activate subscription
            subscription = payment.subscription
            subscription.status = 'active'
            subscription.save()
            
            messages.success(request, 'Payment successful! Your subscription is now active.')
            return redirect('subscriptions:my_subscription')
        else:
            messages.error(request, 'Invalid payment method selected.')
    
    context = {
        'payment': payment,
        'subscription': payment.subscription,
    }
    
    return render(request, 'subscriptions/payment.html', context)


@login_required
def my_subscription(request):
    """
    User's current subscription details
    """
    try:
        subscription = Subscription.objects.get(shop=request.user.shop)
    except Subscription.DoesNotExist:
        subscription = None
    
    context = {
        'subscription': subscription,
        'available_plans': SubscriptionPlan.objects.filter(is_active=True),
    }
    
    return render(request, 'subscriptions/my_subscription.html', context)
