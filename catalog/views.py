from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from .models import MasterCatalog
from .forms import MasterCatalogForm
from core.middleware import role_required
from django.conf import settings


@login_required
@role_required(settings.ROLE_SUPER_ADMIN)
def catalog_list(request):
    """List all medicines in master catalog"""
    query = request.GET.get('q', '')
    medicines = MasterCatalog.objects.filter(is_active=True)
    
    if query:
        medicines = medicines.filter(
            Q(brand_name__icontains=query) |
            Q(generic__icontains=query) |
            Q(manufacturer__icontains=query)
        )
    
    paginator = Paginator(medicines, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'catalog/list.html', {
        'page_obj': page_obj,
        'query': query
    })


@login_required
@role_required(settings.ROLE_SUPER_ADMIN)
def catalog_create(request):
    """Create new medicine in master catalog"""
    if request.method == 'POST':
        form = MasterCatalogForm(request.POST)
        if form.is_valid():
            medicine = form.save(commit=False)
            # Auto-generate brand_id and slug
            last_medicine = MasterCatalog.objects.order_by('-brand_id').first()
            medicine.brand_id = (last_medicine.brand_id + 1) if last_medicine else 1
            medicine.slug = f"{medicine.brand_name.lower().replace(' ', '-')}-{medicine.strength.lower().replace(' ', '-')}"
            medicine.save()
            messages.success(request, f'{medicine.brand_name} added to catalog!')
            return redirect('catalog:list')
    else:
        form = MasterCatalogForm()
    
    return render(request, 'catalog/form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required(settings.ROLE_SUPER_ADMIN)
def catalog_update(request, pk):
    """Update medicine in master catalog"""
    medicine = get_object_or_404(MasterCatalog, pk=pk)
    
    if request.method == 'POST':
        form = MasterCatalogForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f'{medicine.brand_name} updated!')
            return redirect('catalog:list')
    else:
        form = MasterCatalogForm(instance=medicine)
    
    return render(request, 'catalog/form.html', {'form': form, 'action': 'Update', 'medicine': medicine})


@login_required
@role_required(settings.ROLE_SUPER_ADMIN)
def catalog_delete(request, pk):
    """Delete medicine from master catalog (soft delete)"""
    medicine = get_object_or_404(MasterCatalog, pk=pk)
    medicine.is_active = False
    medicine.save()
    messages.success(request, f'{medicine.brand_name} deleted!')
    return redirect('catalog:list')



