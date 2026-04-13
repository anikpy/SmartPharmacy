from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import Customer, Transaction, TransactionItem, CustomerDue
from .forms import CustomerForm, POSForm
from inventory.models import ShopInventory
from core.middleware import role_required, shop_required
from django.conf import settings


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
                    subtotal=subtotal,
                    discount=form.cleaned_data.get('discount', 0),
                    tax=tax,
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
            Q(customer__name__icontains=query)
        )
    
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
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def customer_list(request):
    """List all customers"""
    query = request.GET.get('q', '')
    customers = Customer.objects.filter(shop=request.user)
    
    if query:
        customers = customers.filter(name__icontains=query)
    
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
