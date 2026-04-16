from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, F
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta
import json
from .models import Customer, Transaction, TransactionItem, CustomerDue, Supplier
from .forms import CustomerForm, POSForm, SupplierForm
from inventory.models import ShopInventory
from core.middleware import role_required, shop_required
from django.conf import settings

User = get_user_model()


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def pos(request):
    """Point of Sale interface with keyboard shortcuts"""
    # Get cart from session
    cart = request.session.get('pos_cart', [])

    # Calculate totals
    subtotal = sum(item['total'] for item in cart)
    discount = 0
    tax = 0
    total = subtotal - discount + tax

    if request.method == 'POST':
        form = POSForm(request.POST, shop=request.user)
        if form.is_valid() and cart:
            with transaction.atomic():
                # Calculate discount based on type
                discount_type = form.cleaned_data.get('discount_type', 'percentage')
                discount_value = form.cleaned_data.get('discount', 0) or 0

                # Convert subtotal to Decimal for calculation
                subtotal_decimal = Decimal(str(subtotal))

                if discount_type == 'percentage':
                    discount = subtotal_decimal * (Decimal(str(discount_value)) / Decimal('100'))
                else:
                    discount = Decimal(str(discount_value))

                total = subtotal_decimal - discount + Decimal(str(tax))

                # Create or get customer
                customer = form.cleaned_data.get('customer')
                if not customer and form.cleaned_data.get('customer_name'):
                    customer = Customer.objects.create(
                        name=form.cleaned_data['customer_name'],
                        phone=form.cleaned_data.get('customer_phone', ''),
                        address=form.cleaned_data.get('customer_address', ''),
                        shop=request.user
                    )
                
                # Create transaction
                invoice = Transaction.objects.create(
                    shop=request.user,
                    customer=customer,
                    subtotal=subtotal_decimal,
                    discount=discount,
                    tax=Decimal(str(tax)),
                    total=total,
                    payment_method=form.cleaned_data['payment_method'],
                    notes=form.cleaned_data.get('notes', ''),
                    created_by=request.user
                )
                
                # Create transaction items and update inventory
                for item in cart:
                    inventory = get_object_or_404(ShopInventory, pk=item['inventory_id'], shop=request.user)
                    
                    # Create transaction item
                    TransactionItem.objects.create(
                        transaction=invoice,
                        inventory=inventory,
                        medicine_name=inventory.master_medicine.brand_name,
                        generic_name=inventory.master_medicine.generic,
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        total_price=item['total'],
                        batch_number=inventory.batch_number
                    )
                    
                    # Update inventory
                    inventory.stock_quantity -= item['quantity']
                    inventory.save()
                
                # Create due record if payment method is credit
                if form.cleaned_data['payment_method'] == 'credit' and customer:
                    CustomerDue.objects.create(
                        customer=customer,
                        transaction=invoice,
                        amount=total
                    )
                
                # Clear cart
                request.session['pos_cart'] = []
                
                messages.success(request, f'Transaction completed! Invoice: {invoice.invoice_number}')
                return redirect('sales:detail', pk=invoice.pk)
    else:
        form = POSForm(shop=request.user)
    
    return render(request, 'sales/pos.html', {
        'cart': cart,
        'subtotal': subtotal,
        'discount': discount,
        'tax': tax,
        'total': total,
        'form': form
    })


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def pos_add_item(request):
    """Add item to POS cart via AJAX"""
    inventory_id = request.GET.get('inventory_id')
    quantity = int(request.GET.get('quantity', 1))
    
    inventory = get_object_or_404(ShopInventory, pk=inventory_id, shop=request.user)
    
    if inventory.stock_quantity < quantity:
        return JsonResponse({'success': False, 'error': 'Insufficient stock'})
    
    cart = request.session.get('pos_cart', [])
    
    # Check if item already in cart
    for item in cart:
        if item['inventory_id'] == inventory_id:
            item['quantity'] += quantity
            item['total'] = item['quantity'] * item['unit_price']
            break
    else:
        cart.append({
            'inventory_id': inventory.id,
            'medicine_name': inventory.master_medicine.brand_name,
            'generic': inventory.master_medicine.generic,
            'strength': inventory.master_medicine.strength,
            'quantity': quantity,
            'unit_price': float(inventory.local_price),
            'total': quantity * float(inventory.local_price),
            'batch_number': inventory.batch_number
        })
    
    request.session['pos_cart'] = cart
    
    return JsonResponse({'success': True, 'cart': cart})


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def pos_remove_item(request, item_id):
    """Remove item from POS cart"""
    cart = request.session.get('pos_cart', [])
    cart = [item for item in cart if item['inventory_id'] != item_id]
    request.session['pos_cart'] = cart

    return JsonResponse({'success': True, 'cart': cart})


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def search_customer_by_phone(request):
    """Search customer by phone number via AJAX"""
    phone = request.GET.get('phone', '').strip()
    if not phone:
        return JsonResponse({'success': False, 'error': 'Phone number required'})

    customers = Customer.objects.filter(
        shop=request.user,
        phone__icontains=phone
    )

    results = []
    for customer in customers:
        # Calculate total purchases
        total_purchases = Transaction.objects.filter(customer=customer).aggregate(
            total=Sum('total')
        )['total'] or 0

        results.append({
            'id': customer.id,
            'name': customer.name,
            'phone': customer.phone,
            'address': customer.address,
            'total_purchases': float(total_purchases),
            'total_due': float(customer.total_due)
        })

    return JsonResponse({'success': True, 'results': results})


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def pos_complete(request):
    """Complete POS transaction"""
    # This is handled in the pos view
    return redirect('sales:pos')


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def transaction_list(request):
    """List all transactions for the shop"""
    query = request.GET.get('q', '')
    transactions = Transaction.objects.filter(shop=request.user)

    if query:
        transactions = transactions.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(customer__phone__icontains=query)
        ).order_by('-created_at')
    else:
        transactions = transactions.order_by('-created_at')

    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sales/transaction_list.html', {'page_obj': page_obj, 'query': query})


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def transaction_detail(request, pk):
    """View transaction details"""
    transaction = get_object_or_404(Transaction, pk=pk, shop=request.user)
    return render(request, 'sales/transaction_detail.html', {'transaction': transaction})


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def customer_transaction_history(request, customer_id):
    """Get transaction history for a customer (AJAX endpoint)"""
    customer = get_object_or_404(Customer, pk=customer_id, shop=request.user)
    transactions = Transaction.objects.filter(
        shop=request.user,
        customer=customer
    ).order_by('-created_at')

    results = []
    for t in transactions:
        results.append({
            'id': t.id,
            'invoice_number': t.invoice_number,
            'date': t.created_at.strftime('%Y-%m-%d %H:%M'),
            'total': float(t.total),
            'status': t.status,
            'payment_method': t.get_payment_method_display()
        })

    return JsonResponse({'success': True, 'results': results})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def transaction_delete(request, pk):
    """Delete a transaction (only for shop owner)"""
    transaction = get_object_or_404(Transaction, pk=pk, shop=request.user)
    if request.method == 'POST':
        # Restore inventory stock
        with transaction.atomic():
            for item in transaction.items.all():
                if item.inventory:
                    item.inventory.stock_quantity += item.quantity
                    item.inventory.save()

            # Delete transaction
            transaction.delete()
            messages.success(request, f'Transaction {transaction.invoice_number} deleted and inventory restored!')
            return redirect('sales:list')
    return render(request, 'sales/transaction_confirm_delete.html', {'transaction': transaction})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def customer_delete(request, pk):
    """Delete a customer (only for shop owner)"""
    customer = get_object_or_404(Customer, pk=pk, shop=request.user)
    if request.method == 'POST':
        # Check if customer has transactions
        transaction_count = Transaction.objects.filter(customer=customer).count()
        if transaction_count > 0:
            messages.error(request, f'Cannot delete customer with {transaction_count} transactions. Delete transactions first.')
            return redirect('sales:customer_list')
        
        customer.delete()
        messages.success(request, f'Customer {customer.name} deleted!')
        return redirect('sales:customer_list')
    return render(request, 'sales/customer_confirm_delete.html', {'customer': customer})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def customer_list(request):
    """List all customers"""
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(shop=request.user)

    if query:
        # Search by phone number first (unique identifier), then by name
        customers = customers.filter(
            Q(phone__icontains=query) | Q(name__icontains=query)
        ).order_by('-phone__icontains', 'name')

    paginator = Paginator(customers, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sales/customer_list.html', {'page_obj': page_obj, 'query': query})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def customer_create(request):
    """Create new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.shop = request.user
            customer.save()
            messages.success(request, f'Customer {customer.name} created!')
            return redirect('sales:customer_list')
    else:
        form = CustomerForm()
    
    return render(request, 'sales/customer_form.html', {'form': form})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def customer_dues(request, pk):
    """View customer dues"""
    customer = get_object_or_404(Customer, pk=pk, shop=request.user)
    dues = customer.dues.filter(is_paid=False)
    return render(request, 'sales/customer_dues.html', {'customer': customer, 'dues': dues})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def pay_due(request, pk):
    """Pay customer due"""
    due = get_object_or_404(CustomerDue, pk=pk, customer__shop=request.user)
    due.is_paid = True
    due.paid_date = timezone.now()
    due.save()
    messages.success(request, f'Due of {due.amount} paid!')
    return redirect('sales:customer_dues', pk=due.customer.pk)


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def supplier_list(request):
    """List all suppliers"""
    query = request.GET.get('q', '')
    suppliers = Supplier.objects.filter(shop=request.user)

    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query)
        )

    paginator = Paginator(suppliers, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'sales/supplier_list.html', {'page_obj': page_obj, 'query': query})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def supplier_create(request):
    """Create new supplier"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.shop = request.user
            supplier.save()
            messages.success(request, f'Supplier {supplier.name} created!')
            return redirect('sales:supplier_list')
    else:
        form = SupplierForm()

    return render(request, 'sales/supplier_form.html', {'form': form})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def supplier_update(request, pk):
    """Update supplier"""
    supplier = get_object_or_404(Supplier, pk=pk, shop=request.user)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f'Supplier {supplier.name} updated!')
            return redirect('sales:supplier_list')
    else:
        form = SupplierForm(instance=supplier)

    return render(request, 'sales/supplier_form.html', {'form': form, 'supplier': supplier})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def supplier_delete(request, pk):
    """Delete supplier"""
    supplier = get_object_or_404(Supplier, pk=pk, shop=request.user)
    if request.method == 'POST':
        supplier.delete()
        messages.success(request, f'Supplier {supplier.name} deleted!')
        return redirect('sales:supplier_list')
    return render(request, 'sales/supplier_confirm_delete.html', {'supplier': supplier})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def dashboard_analytics(request):
    """Dashboard with sales analytics and KPIs"""
    # Get date range (default to last 30 days)
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    # Sales data
    transactions = Transaction.objects.filter(
        shop=request.user,
        status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    # KPIs
    total_sales = transactions.aggregate(total=Sum('total'))['total'] or Decimal('0')
    total_transactions = transactions.count()
    avg_transaction_value = total_sales / total_transactions if total_transactions > 0 else Decimal('0')

    # Daily sales for chart
    daily_sales = []
    for i in range(days):
        date = end_date - timedelta(days=i)
        day_sales = transactions.filter(created_at__date=date).aggregate(total=Sum('total'))['total'] or Decimal('0')
        daily_sales.append({
            'date': date.strftime('%Y-%m-%d'),
            'sales': float(day_sales)
        })
    daily_sales.reverse()

    # Top selling medicines
    top_medicines = TransactionItem.objects.filter(
        transaction__shop=request.user,
        transaction__status='completed',
        transaction__created_at__date__gte=start_date
    ).values('medicine_name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:10]

    # Low stock alerts
    low_stock_items = ShopInventory.objects.filter(
        shop=request.user,
        stock_quantity__lte=F('low_stock_threshold'),
        is_active=True
    ).select_related('master_medicine')

    # Expiring soon (within 30 days)
    expiring_soon = ShopInventory.objects.filter(
        shop=request.user,
        expiry_date__lte=end_date + timedelta(days=30),
        expiry_date__gte=end_date,
        is_active=True
    ).select_related('master_medicine').order_by('expiry_date')

    # Payment method breakdown
    payment_methods = transactions.values('payment_method').annotate(
        count=Sum('total'),
        total=Sum('total')
    )

    context = {
        'total_sales': total_sales,
        'total_transactions': total_transactions,
        'avg_transaction_value': avg_transaction_value,
        'daily_sales_json': json.dumps(daily_sales),
        'top_medicines': top_medicines,
        'low_stock_items': low_stock_items,
        'expiring_soon': expiring_soon,
        'payment_methods': payment_methods,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'sales/dashboard_analytics.html', context)


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def expiry_management(request):
    """Expiry date management for medicines"""
    today = timezone.now().date()

    # Get filter parameters
    days = int(request.GET.get('days', 90))
    end_date = today + timedelta(days=days)

    # Filter by expiry date
    expiring_items = ShopInventory.objects.filter(
        shop=request.user,
        expiry_date__lte=end_date,
        expiry_date__gte=today,
        is_active=True
    ).select_related('master_medicine').order_by('expiry_date')

    # Pagination
    paginator = Paginator(expiring_items, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate discount suggestions and days to expiry for paginated items
    for item in page_obj:
        days_to_expiry = (item.expiry_date - today).days
        item.days_to_expiry = days_to_expiry

        if days_to_expiry <= 7:
            item.suggested_discount = 30  # 30% discount for items expiring within 7 days
        elif days_to_expiry <= 14:
            item.suggested_discount = 20  # 20% discount for items expiring within 14 days
        elif days_to_expiry <= 30:
            item.suggested_discount = 15  # 15% discount for items expiring within 30 days
        elif days_to_expiry <= 60:
            item.suggested_discount = 10  # 10% discount for items expiring within 60 days
        else:
            item.suggested_discount = None

    # Categorize by urgency (use all items for counts)
    critical = expiring_items.filter(expiry_date__lte=today + timedelta(days=30))
    warning = expiring_items.filter(expiry_date__gt=today + timedelta(days=30), expiry_date__lte=today + timedelta(days=60))
    info = expiring_items.filter(expiry_date__gt=today + timedelta(days=60))

    context = {
        'page_obj': page_obj,
        'critical_count': critical.count(),
        'warning_count': warning.count(),
        'info_count': info.count(),
        'days': days,
        'today': today,
    }

    return render(request, 'sales/expiry_management.html', context)


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def reports_profit_loss(request):
    """Profit/loss report"""
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().date().replace(day=1)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()

    # Get transactions in date range
    transactions = Transaction.objects.filter(
        shop=request.user,
        status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).order_by('-created_at')

    # Pagination
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate totals (use all transactions, not just paginated)
    all_transactions = Transaction.objects.filter(
        shop=request.user,
        status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    total_revenue = all_transactions.aggregate(total=Sum('total'))['total'] or Decimal('0')
    total_discount = all_transactions.aggregate(total=Sum('discount'))['total'] or Decimal('0')
    total_tax = all_transactions.aggregate(total=Sum('tax'))['total'] or Decimal('0')
    total_subtotal = all_transactions.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')

    # Calculate profit (simplified - revenue without cost tracking)
    # In production, you'd track cost price and calculate actual profit
    profit = total_subtotal - total_discount

    context = {
        'page_obj': page_obj,
        'total_revenue': total_revenue,
        'total_discount': total_discount,
        'total_tax': total_tax,
        'total_subtotal': total_subtotal,
        'profit': profit,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'sales/reports_profit_loss.html', context)


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def reports_staff_performance(request):
    """Staff performance report"""
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().date().replace(day=1)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()

    # Get staff users
    staff_users = User.objects.filter(
        shop=request.user.shop,
        role=settings.ROLE_SHOP_WORKER
    )

    # Calculate performance per staff
    staff_performance = []
    for staff in staff_users:
        transactions = Transaction.objects.filter(
            shop=request.user,
            created_by=staff,
            status='completed',
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )

        total_sales = transactions.aggregate(total=Sum('total'))['total'] or Decimal('0')
        transaction_count = transactions.count()

        staff_performance.append({
            'staff': staff,
            'total_sales': total_sales,
            'transaction_count': transaction_count,
            'avg_transaction': total_sales / transaction_count if transaction_count > 0 else Decimal('0'),
        })

    context = {
        'staff_performance': staff_performance,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'sales/reports_staff_performance.html', context)


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def reports_tax(request):
    """Tax report"""
    # Get date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        start_date = timezone.now().date().replace(day=1)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    else:
        end_date = timezone.now().date()

    # Get transactions
    transactions = Transaction.objects.filter(
        shop=request.user,
        status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    ).order_by('-created_at')

    # Pagination
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate tax totals (use all transactions, not just paginated)
    all_transactions = Transaction.objects.filter(
        shop=request.user,
        status='completed',
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )

    total_tax = all_transactions.aggregate(total=Sum('tax'))['total'] or Decimal('0')
    total_revenue = all_transactions.aggregate(total=Sum('total'))['total'] or Decimal('0')

    # Group by payment method
    tax_by_method = all_transactions.values('payment_method').annotate(
        tax_total=Sum('tax'),
        revenue_total=Sum('total')
    )

    context = {
        'page_obj': page_obj,
        'total_tax': total_tax,
        'total_revenue': total_revenue,
        'tax_by_method': tax_by_method,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'sales/reports_tax.html', context)


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def reports_inventory(request):
    """Inventory valuation report"""
    # Get all inventory
    inventory = ShopInventory.objects.filter(
        shop=request.user,
        is_active=True
    ).select_related('master_medicine').order_by('master_medicine__brand_name')

    # Pagination
    paginator = Paginator(inventory, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate totals (use all inventory, not just paginated)
    total_items = inventory.count()
    total_stock = inventory.aggregate(total=Sum('stock_quantity'))['total'] or 0
    total_value = Decimal('0')

    for item in inventory:
        total_value += item.local_price * item.stock_quantity

    # Low stock items
    low_stock = inventory.filter(stock_quantity__lte=F('low_stock_threshold'))

    # Expiring items
    today = timezone.now().date()
    expiring = inventory.filter(
        expiry_date__lte=today + timedelta(days=90),
        expiry_date__gte=today
    )

    context = {
        'page_obj': page_obj,
        'total_items': total_items,
        'total_stock': total_stock,
        'total_value': total_value,
        'low_stock': low_stock,
        'expiring': expiring,
    }

    return render(request, 'sales/reports_inventory.html', context)
