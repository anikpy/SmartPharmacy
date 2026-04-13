from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from .models import MasterCatalog
from .forms import MasterCatalogForm, CSVImportForm
from core.middleware import role_required
from django.conf import settings
import csv
import io


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


@login_required
@role_required(settings.ROLE_SUPER_ADMIN)
def import_csv(request):
    """Import medicines from CSV file"""
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('catalog:import_csv')
            
            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            next(io_string)  # Skip header
            
            count = 0
            for row in csv.reader(io_string):
                if len(row) >= 10:
                    MasterCatalog.objects.create(
                        brand_id=int(row[0]) if row[0] else 0,
                        brand_name=row[1] if row[1] else '',
                        type=row[2] if row[2] else 'allopathic',
                        slug=row[3] if row[3] else '',
                        dosage_form=row[4] if row[4] else 'tablet',
                        generic=row[5] if row[5] else '',
                        strength=row[6] if row[6] else '',
                        manufacturer=row[7] if row[7] else '',
                        package_container=row[8] if row[8] else '',
                        package_size=row[9] if row[9] else ''
                    )
                    count += 1
            
            messages.success(request, f'{count} medicines imported successfully!')
            return redirect('catalog:list')
    else:
        form = CSVImportForm()
    
    return render(request, 'catalog/import_csv.html', {'form': form})
