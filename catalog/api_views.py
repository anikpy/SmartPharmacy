from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import MasterCatalog
import json


@login_required
def medicine_search_api(request):
    """
    AJAX API for real-time medicine search with autocomplete
    Returns JSON with medicine suggestions
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Search in brand name, generic name, and manufacturer
    medicines = MasterCatalog.objects.filter(
        Q(brand_name__icontains=query) | 
        Q(generic__icontains=query) |
        Q(manufacturer__icontains=query),
        is_active=True
    ).select_related().values(
        'id', 'brand_name', 'generic', 'strength', 'manufacturer', 
        'dosage_form', 'type', 'package_size'
    )[:20]  # Limit to 20 results for performance
    
    results = []
    for med in medicines:
        # Create display text for suggestions
        display_text = f"{med['brand_name']}"
        if med['strength']:
            display_text += f" {med['strength']}"
        if med['generic'] and med['generic'] != med['brand_name']:
            display_text += f" ({med['generic']})"
        
        results.append({
            'id': med['id'],
            'brand_name': med['brand_name'],
            'generic': med['generic'],
            'strength': med['strength'],
            'manufacturer': med['manufacturer'],
            'dosage_form': med['dosage_form'],
            'type': med['type'],
            'package_size': med['package_size'],
            'display_text': display_text,
            'search_text': f"{med['brand_name']} {med['generic']} {med['manufacturer']}".lower()
        })
    
    return JsonResponse({
        'results': results,
        'count': len(results),
        'query': query
    })


@login_required 
def medicine_details_api(request, medicine_id):
    """
    Get detailed information about a specific medicine
    """
    try:
        medicine = MasterCatalog.objects.get(id=medicine_id, is_active=True)
        
        data = {
            'id': medicine.id,
            'brand_name': medicine.brand_name,
            'generic': medicine.generic,
            'strength': medicine.strength,
            'manufacturer': medicine.manufacturer,
            'dosage_form': medicine.get_dosage_form_display(),
            'type': medicine.get_type_display(),
            'package_container': medicine.package_container,
            'package_size': medicine.package_size,
            'slug': medicine.slug,
        }
        
        return JsonResponse({
            'success': True,
            'medicine': data
        })
        
    except MasterCatalog.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Medicine not found'
        }, status=404)


@login_required
def medicine_search_suggestions(request):
    """
    Get search suggestions for typeahead functionality
    Returns top suggestions based on popularity/usage
    """
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        # Return popular medicines when query is short
        medicines = MasterCatalog.objects.filter(
            is_active=True
        ).order_by('brand_name')[:10]
    else:
        # Search and rank by relevance
        medicines = MasterCatalog.objects.filter(
            Q(brand_name__istartswith=query) | 
            Q(generic__istartswith=query)
        ).filter(is_active=True).order_by('brand_name')[:10]
    
    suggestions = [
        {
            'value': med.brand_name,
            'label': f"{med.brand_name} {med.strength or ''}".strip(),
            'id': med.id
        }
        for med in medicines
    ]
    
    return JsonResponse({'suggestions': suggestions})
