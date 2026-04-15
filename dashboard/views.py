from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from core.middleware import role_required
from django.conf import settings
from users.models import Shop, User
from catalog.models import MasterCatalog
from inventory.models import ShopInventory
from sales.models import Transaction


@login_required
@role_required(settings.ROLE_SUPER_ADMIN)
def super_admin_dashboard(request):
    """Super Admin Dashboard with platform-wide analytics"""
    total_shops = Shop.objects.filter(is_active=True).count()
    total_medicines = MasterCatalog.objects.filter(is_active=True).count()
    total_users = User.objects.count()
    
    # Recent shops with their owners
    recent_shops = Shop.objects.filter(is_active=True).prefetch_related('staff').order_by('-created_at')[:5]
    
    # Get shop owners for each shop
    for shop in recent_shops:
        shop.owner = User.objects.filter(shop=shop, role=settings.ROLE_SHOP_OWNER).first()
    
    # User distribution by role
    user_distribution = {
        'super_admin': User.objects.filter(role=settings.ROLE_SUPER_ADMIN).count(),
        'shop_owners': User.objects.filter(role=settings.ROLE_SHOP_OWNER).count(),
        'shop_workers': User.objects.filter(role=settings.ROLE_SHOP_WORKER).count(),
    }
    
    return render(request, 'dashboard/super_admin.html', {
        'total_shops': total_shops,
        'total_medicines': total_medicines,
        'total_users': total_users,
        'recent_shops': recent_shops,
        'user_distribution': user_distribution,
    })


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
def shop_owner_dashboard(request):
    """Shop Owner Dashboard with shop-specific analytics"""
    if not request.user.shop:
        return render(request, 'dashboard/no_shop.html')
    
    # Today's sales
    today = timezone.now().date()
    today_sales = Transaction.objects.filter(
        shop=request.user,
        created_at__date=today,
        status='completed'
    )

    today_revenue = today_sales.aggregate(Sum('total'))['total__sum'] or 0
    today_transactions = today_sales.count()

    # This month's sales
    month_start = today.replace(day=1)
    month_sales = Transaction.objects.filter(
        shop=request.user,
        created_at__date__gte=month_start,
        status='completed'
    )

    month_revenue = month_sales.aggregate(Sum('total'))['total__sum'] or 0
    
    # Low stock alerts
    low_stock_count = ShopInventory.objects.filter(
        shop=request.user,
        is_active=True
    ).filter(
        stock_quantity__lte=F('low_stock_threshold')
    ).count()

    # Total inventory value
    inventory_value = ShopInventory.objects.filter(
        shop=request.user,
        is_active=True
    ).aggregate(
        total_value=Sum(F('stock_quantity') * F('local_price'))
    )['total_value'] or 0
    
    # Staff count
    staff_count = User.objects.filter(shop=request.user.shop).count()
    
    return render(request, 'dashboard/shop_owner.html', {
        'today_revenue': today_revenue,
        'today_transactions': today_transactions,
        'month_revenue': month_revenue,
        'low_stock_count': low_stock_count,
        'inventory_value': inventory_value,
        'staff_count': staff_count,
    })


@login_required
@role_required(settings.ROLE_SHOP_WORKER)
def shop_worker_dashboard(request):
    """Shop Worker Dashboard - redirects to POS"""
    return render(request, 'dashboard/shop_worker.html')
