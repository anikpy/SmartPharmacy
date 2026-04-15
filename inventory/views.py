from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import ShopInventory, StockAdjustment, ShopCustomMedicine, ShopCustomMedicineInventory
from .forms import ShopInventoryForm, AddToInventoryForm, ShopCustomMedicineInventoryForm, AddCustomMedicineToInventoryForm
from core.middleware import role_required, shop_required
from django.conf import settings
from catalog.models import MasterCatalog
from decimal import Decimal


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def inventory_list(request):
    """List shop's inventory - filtered by user's shop (both master catalog and custom medicines)"""
    query = request.GET.get('q', '')
    source = request.GET.get('source', 'all')  # 'all', 'master', 'custom'

    # Get master catalog inventory
    master_inventory = ShopInventory.objects.filter(shop=request.user, is_active=True).select_related('master_medicine')

    # Get custom medicine inventory
    custom_inventory = ShopCustomMedicineInventory.objects.filter(shop=request.user, is_active=True).select_related('custom_medicine')

    if query:
        master_inventory = master_inventory.filter(
            Q(master_medicine__brand_name__icontains=query) |
            Q(master_medicine__generic__icontains=query) |
            Q(batch_number__icontains=query)
        )
        custom_inventory = custom_inventory.filter(
            Q(custom_medicine__brand_name__icontains=query) |
            Q(custom_medicine__generic__icontains=query) |
            Q(batch_number__icontains=query)
        )

    # Filter by source if specified
    if source == 'master':
        inventory_list = master_inventory
    elif source == 'custom':
        inventory_list = custom_inventory
    else:
        # Combine both and sort by created_at
        inventory_list = list(master_inventory) + list(custom_inventory)
        inventory_list.sort(key=lambda x: x.created_at, reverse=True)

    paginator = Paginator(inventory_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate total stock value
    total_value = (master_inventory.aggregate(Sum('local_price'))['local_price__sum'] or 0) + \
                  (custom_inventory.aggregate(Sum('local_price'))['local_price__sum'] or 0)

    return render(request, 'inventory/list.html', {
        'page_obj': page_obj,
        'query': query,
        'total_value': total_value,
        'source': source
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
    
    return JsonResponse({'results': results})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def search_master_catalog(request):
    """AJAX endpoint for searching medicines - returns both master catalog and custom medicines"""
    query = request.GET.get('q', '').strip()

    if not query or len(query) < 1:
        return JsonResponse({'results': []})

    results = []

    # Search Master Catalog medicines
    master_medicines = MasterCatalog.objects.filter(
        is_active=True
    ).filter(
        Q(brand_name__icontains=query) |
        Q(generic__icontains=query) |
        Q(manufacturer__icontains=query)
    ).values(
        'id', 'brand_name', 'generic', 'strength', 'dosage_form', 
        'type', 'manufacturer', 'package_container', 'package_size', 'suggested_price'
    )[:10]

    for medicine in master_medicines:
        results.append({
            'id': medicine['id'],
            'brand_name': medicine['brand_name'],
            'generic': medicine['generic'],
            'strength': medicine['strength'],
            'dosage_form': medicine['dosage_form'],
            'type': medicine['type'],
            'manufacturer': medicine['manufacturer'],
            'package_container': medicine['package_container'],
            'package_size': medicine['package_size'],
            'suggested_price': str(medicine['suggested_price']),
            'source': 'master_catalog',
        })

    # Search Custom Medicines for this shop
    custom_medicines = ShopCustomMedicine.objects.filter(
        shop=request.user,
        is_active=True
    ).filter(
        Q(brand_name__icontains=query) |
        Q(generic__icontains=query) |
        Q(manufacturer__icontains=query)
    ).values(
        'id', 'brand_name', 'generic', 'strength', 'dosage_form', 
        'manufacturer', 'suggested_price'
    )[:10]

    for medicine in custom_medicines:
        results.append({
            'id': medicine['id'],
            'brand_name': medicine['brand_name'],
            'generic': medicine['generic'],
            'strength': medicine['strength'],
            'dosage_form': medicine['dosage_form'],
            'type': 'allopathic',
            'manufacturer': medicine['manufacturer'],
            'package_container': '',
            'package_size': '',
            'suggested_price': str(medicine['suggested_price']),
            'source': 'custom',
        })

    # Limit total results to 20
    results = results[:20]

    return JsonResponse({'results': results})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def add_custom_medicine(request):
    """Add a custom medicine for the shop that's not in master catalog"""
    if request.method == 'POST':
        try:
            brand_name = request.POST.get('brand_name', '').strip()
            generic = request.POST.get('generic', '').strip()
            strength = request.POST.get('strength', '').strip()
            dosage_form = request.POST.get('dosage_form', 'tablet').strip()
            manufacturer = request.POST.get('manufacturer', '').strip()
            suggested_price = request.POST.get('suggested_price', '0.00').strip()

            # Validate required fields
            if not all([brand_name, generic, strength]):
                return JsonResponse({'success': False, 'error': 'Brand name, generic name, and strength are required'})

            # Check if already exists for this shop
            existing = ShopCustomMedicine.objects.filter(
                shop=request.user,
                brand_name=brand_name,
                strength=strength
            ).exists()

            if existing:
                return JsonResponse({'success': False, 'error': 'This medicine already exists in your custom medicines'})

            # Create custom medicine
            custom_medicine = ShopCustomMedicine.objects.create(
                shop=request.user,
                brand_name=brand_name,
                generic=generic,
                strength=strength,
                dosage_form=dosage_form,
                manufacturer=manufacturer,
                suggested_price=Decimal(suggested_price) if suggested_price else Decimal('0.00'),
                is_active=True
            )

            messages.success(request, f'Custom medicine "{brand_name}" added successfully!')
            return JsonResponse({'success': True, 'medicine_id': custom_medicine.id, 'message': 'Medicine added successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request - show form
    return render(request, 'inventory/add_custom_medicine.html')


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def my_custom_medicines(request):
    """List all custom medicines for the shop"""
    medicines = ShopCustomMedicine.objects.filter(
        shop=request.user,
        is_active=True
    ).order_by('-created_at')

    paginator = Paginator(medicines, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/custom_medicines_list.html', {'page_obj': page_obj})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def custom_inventory_add(request):
    """Add custom medicine to shop inventory"""
    medicine_id = request.GET.get('medicine_id')

    if request.method == 'POST':
        form = AddCustomMedicineToInventoryForm(request.user, request.POST)
        if form.is_valid():
            inventory = ShopCustomMedicineInventory.objects.create(
                shop=request.user,
                custom_medicine=form.cleaned_data['custom_medicine'],
                local_price=form.cleaned_data['local_price'],
                stock_quantity=form.cleaned_data['stock_quantity'],
                expiry_date=form.cleaned_data['expiry_date'],
                batch_number=form.cleaned_data['batch_number']
            )

            # Create stock adjustment record
            StockAdjustment.objects.create(
                custom_inventory=inventory,
                adjustment_type='purchase',
                quantity=form.cleaned_data['stock_quantity'],
                previous_quantity=0,
                new_quantity=form.cleaned_data['stock_quantity'],
                reason='Initial stock addition',
                adjusted_by=request.user
            )

            messages.success(request, f'{inventory.custom_medicine.brand_name} added to inventory!')
            return redirect('inventory:custom_inventory_list')
    else:
        form = AddCustomMedicineToInventoryForm(request.user)
        # Pre-select medicine if medicine_id is provided
        if medicine_id:
            try:
                medicine = ShopCustomMedicine.objects.get(id=medicine_id, shop=request.user, is_active=True)
                form.fields['custom_medicine'].initial = medicine
            except ShopCustomMedicine.DoesNotExist:
                pass

    return render(request, 'inventory/custom_inventory_form.html', {'form': form, 'action': 'Add'})


@login_required
@role_required(settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER)
@shop_required
def custom_inventory_list(request):
    """List shop's custom medicine inventory"""
    query = request.GET.get('q', '')
    inventory = ShopCustomMedicineInventory.objects.filter(
        shop=request.user,
        is_active=True
    ).select_related('custom_medicine')

    if query:
        inventory = inventory.filter(
            Q(custom_medicine__brand_name__icontains=query) |
            Q(custom_medicine__generic__icontains=query) |
            Q(batch_number__icontains=query)
        )

    paginator = Paginator(inventory, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate total stock value
    total_value = inventory.aggregate(Sum('local_price'))['local_price__sum'] or 0

    return render(request, 'inventory/custom_inventory_list.html', {
        'page_obj': page_obj,
        'query': query,
        'total_value': total_value
    })


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def custom_inventory_update(request, pk):
    """Update custom medicine inventory item"""
    inventory = get_object_or_404(ShopCustomMedicineInventory, pk=pk, shop=request.user)

    if request.method == 'POST':
        form = ShopCustomMedicineInventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            old_quantity = inventory.stock_quantity
            updated_inventory = form.save()

            # Create stock adjustment if quantity changed
            if old_quantity != updated_inventory.stock_quantity:
                StockAdjustment.objects.create(
                    custom_inventory=updated_inventory,
                    adjustment_type='adjustment',
                    quantity=updated_inventory.stock_quantity - old_quantity,
                    previous_quantity=old_quantity,
                    new_quantity=updated_inventory.stock_quantity,
                    reason='Manual stock adjustment',
                    adjusted_by=request.user
                )

            messages.success(request, f'{inventory.custom_medicine.brand_name} updated!')
            return redirect('inventory:custom_inventory_list')
    else:
        form = ShopCustomMedicineInventoryForm(instance=inventory)

    return render(request, 'inventory/custom_inventory_form.html', {'form': form, 'action': 'Update', 'inventory': inventory})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
@shop_required
def custom_inventory_delete(request, pk):
    """Delete custom medicine inventory item (soft delete)"""
    inventory = get_object_or_404(ShopCustomMedicineInventory, pk=pk, shop=request.user)
    inventory.is_active = False
    inventory.save()
    messages.success(request, f'{inventory.custom_medicine.brand_name} removed from inventory!')
    return redirect('inventory:custom_inventory_list')
