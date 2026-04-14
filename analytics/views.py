from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import month_name
from sales.models import Transaction, TransactionItem
from inventory.models import ShopInventory
from .models import AnalyticsSnapshot, SalesAnalytics


@login_required
def analytics_dashboard(request):
    """
    Main analytics dashboard with charts and KPIs
    """
    shop = request.user.shop
    if not shop:
        return render(request, 'analytics/no_shop.html')
    
    # Date range for analysis
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Key Performance Indicators
    total_sales = Transaction.objects.filter(
        shop=shop,
        date__range=[start_date, end_date],
        status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    total_transactions = Transaction.objects.filter(
        shop=shop,
        date__range=[start_date, end_date],
        status='completed'
    ).count()
    
    avg_transaction_value = Transaction.objects.filter(
        shop=shop,
        date__range=[start_date, end_date],
        status='completed'
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0
    
    total_inventory_items = ShopInventory.objects.filter(shop=shop).count()
    
    low_stock_items = ShopInventory.objects.filter(
        shop=shop,
        quantity__lte=F('low_stock_threshold')
    ).count()
    
    # Top selling medicines
    top_medicines = TransactionItem.objects.filter(
        transaction__shop=shop,
        transaction__date__range=[start_date, end_date],
        transaction__status='completed'
    ).values(
        'inventory_item__medicine__brand_name',
        'inventory_item__medicine__strength'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_quantity')[:10]
    
    context = {
        'shop': shop,
        'date_range': f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}",
        'kpis': {
            'total_sales': total_sales,
            'total_transactions': total_transactions,
            'avg_transaction_value': avg_transaction_value,
            'total_inventory_items': total_inventory_items,
            'low_stock_items': low_stock_items,
        },
        'top_medicines': top_medicines,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def sales_chart_api(request):
    """
    API endpoint for sales chart data
    """
    shop = request.user.shop
    if not shop:
        return JsonResponse({'error': 'No shop assigned'}, status=400)
    
    period = request.GET.get('period', '30')  # days
    end_date = timezone.now().date()
    
    if period == '7':
        start_date = end_date - timedelta(days=7)
        group_by = 'day'
    elif period == '30':
        start_date = end_date - timedelta(days=30)
        group_by = 'day'
    elif period == '90':
        start_date = end_date - timedelta(days=90)
        group_by = 'week'
    else:
        start_date = end_date - timedelta(days=365)
        group_by = 'month'
    
    # Get daily sales data
    sales_data = Transaction.objects.filter(
        shop=shop,
        date__range=[start_date, end_date],
        status='completed'
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        sales=Sum('total_amount'),
        transactions=Count('id')
    ).order_by('day')
    
    # Format data for charts
    labels = []
    sales_values = []
    transaction_counts = []
    
    for item in sales_data:
        date_obj = datetime.strptime(item['day'], '%Y-%m-%d').date()
        labels.append(date_obj.strftime('%b %d'))
        sales_values.append(float(item['sales'] or 0))
        transaction_counts.append(item['transactions'])
    
    return JsonResponse({
        'labels': labels,
        'datasets': [
            {
                'label': 'Sales ($)',
                'data': sales_values,
                'borderColor': 'rgb(59, 130, 246)',
                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                'tension': 0.4
            },
            {
                'label': 'Transactions',
                'data': transaction_counts,
                'borderColor': 'rgb(16, 185, 129)',
                'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                'tension': 0.4,
                'yAxisID': 'y1'
            }
        ]
    })


@login_required
def inventory_chart_api(request):
    """
    API endpoint for inventory analytics
    """
    shop = request.user.shop
    if not shop:
        return JsonResponse({'error': 'No shop assigned'}, status=400)
    
    # Stock levels by category
    stock_by_form = ShopInventory.objects.filter(shop=shop).values(
        'medicine__dosage_form'
    ).annotate(
        total_items=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]
    
    # Low stock analysis
    low_stock = ShopInventory.objects.filter(
        shop=shop,
        quantity__lte=F('low_stock_threshold')
    ).values(
        'medicine__brand_name',
        'medicine__strength',
        'quantity',
        'low_stock_threshold'
    )[:20]
    
    return JsonResponse({
        'stock_by_form': list(stock_by_form),
        'low_stock_items': list(low_stock),
    })


@login_required
def financial_reports(request):
    """
    Detailed financial reporting page
    """
    shop = request.user.shop
    if not shop:
        return render(request, 'analytics/no_shop.html')
    
    # Monthly revenue breakdown
    monthly_data = []
    for i in range(12):
        date = timezone.now().date().replace(day=1) - timedelta(days=30*i)
        month_start = date.replace(day=1)
        
        if date.month == 12:
            month_end = date.replace(year=date.year+1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = date.replace(month=date.month+1, day=1) - timedelta(days=1)
        
        revenue = Transaction.objects.filter(
            shop=shop,
            date__range=[month_start, month_end],
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_data.append({
            'month': month_name[date.month],
            'year': date.year,
            'revenue': revenue
        })
    
    monthly_data.reverse()  # Show chronologically
    
    context = {
        'shop': shop,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'analytics/financial_reports.html', context)
