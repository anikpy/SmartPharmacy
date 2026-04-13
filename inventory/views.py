from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F
from django.core.paginator import Paginator
from .models import ShopInventory, StockAdjustment
from .forms import ShopInventoryForm, AddToInventoryForm
from core.middleware import role_required, shop_required
from django.conf import settings
from catalog.models import MasterCatalog


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def inventory_list(request):
    """List shop's inventory - filtered by user's shop"""
    query = request.GET.get('q', '')
    inventory = ShopInventory.objects.filter(shop=request.user, is_active=True).select_related('master_medicine')
    
    if query:
        inventory = inventory.filter(
            Q(master_medicine__brand_name__icontains=query) |
            Q(master_medicine__generic__icontains=query) |
            Q(batch_number__icontains=query)
        )
    
    paginator = Paginator(inventory, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate total stock value
    total_value = inventory.aggregate(Sum('local_price'))['local_price__sum'] or 0
    
    return render(request, 'inventory/list.html', {
        'page_obj': page_obj,
        'query': query,
        'total_value': total_value
    })


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def inventory_add(request):
    """Add medicine to shop inventory from master catalog"""
    if request.method == 'POST':
        form = AddToInventoryForm(request.POST)
        if form.is_valid():
            inventory = ShopInventory.objects.create(
                shop=request.user,
                master_medicine=form.cleaned_data['master_medicine'],
                local_price=form.cleaned_data['local_price'],
                stock_quantity=form.cleaned_data['stock_quantity'],
                expiry_date=form.cleaned_data['expiry_date'],
                batch_number=form.cleaned_data['batch_number']
            )
            
            # Create stock adjustment record
            StockAdjustment.objects.create(
                inventory=inventory,
                adjustment_type='purchase',
                quantity=form.cleaned_data['stock_quantity'],
                previous_quantity=0,
                new_quantity=form.cleaned_data['stock_quantity'],
                reason='Initial stock addition',
                adjusted_by=request.user
            )
            
            messages.success(request, f'{inventory.master_medicine.brand_name} added to inventory!')
            return redirect('inventory:list')
    else:
        form = AddToInventoryForm()
    
    return render(request, 'inventory/form.html', {'form': form, 'action': 'Add'})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def inventory_update(request, pk):
    """Update inventory item"""
    inventory = get_object_or_404(ShopInventory, pk=pk, shop=request.user)
    
    if request.method == 'POST':
        form = ShopInventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            old_quantity = inventory.stock_quantity
            updated_inventory = form.save()
            
            # Create stock adjustment if quantity changed
            if old_quantity != updated_inventory.stock_quantity:
                StockAdjustment.objects.create(
                    inventory=updated_inventory,
                    adjustment_type='adjustment',
                    quantity=updated_inventory.stock_quantity - old_quantity,
                    previous_quantity=old_quantity,
                    new_quantity=updated_inventory.stock_quantity,
                    reason='Manual stock adjustment',
                    adjusted_by=request.user
                )
            
            messages.success(request, f'{inventory.master_medicine.brand_name} updated!')
            return redirect('inventory:list')
    else:
        form = ShopInventoryForm(instance=inventory)
    
    return render(request, 'inventory/form.html', {'form': form, 'action': 'Update', 'inventory': inventory})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def inventory_delete(request, pk):
    """Delete inventory item (soft delete)"""
    inventory = get_object_or_404(ShopInventory, pk=pk, shop=request.user)
    inventory.is_active = False
    inventory.save()
    messages.success(request, f'{inventory.master_medicine.brand_name} removed from inventory!')
    return redirect('inventory:list')


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def low_stock_alerts(request):
    """Show low stock items"""
    low_stock_items = ShopInventory.objects.filter(
        shop=request.user,
        is_active=True
    ).filter(
        stock_quantity__lte=F('low_stock_threshold')
    )
    
    return render(request, 'inventory/low_stock.html', {'low_stock_items': low_stock_items})


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def search_medicines(request):
    """AJAX endpoint for searching medicines in inventory"""
    query = request.GET.get('q', '')
    medicines = ShopInventory.objects.filter(
        shop=request.user,
        is_active=True,
        master_medicine__brand_name__icontains=query
    ).select_related('master_medicine')[:10]
    
    results = []
    for item in medicines:
        results.append({
            'id': item.id,
            'name': item.master_medicine.brand_name,
            'generic': item.master_medicine.generic,
            'strength': item.master_medicine.strength,
            'price': str(item.local_price),
            'stock': item.stock_quantity
        })
    
    from django.http import JsonResponse
    return JsonResponse({'results': results})
