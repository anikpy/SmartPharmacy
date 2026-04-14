from django import forms
from .models import MasterCatalog


class MasterCatalogForm(forms.ModelForm):
    class Meta:
        model = MasterCatalog
        fields = ['brand_name', 'type', 'dosage_form', 'generic', 'strength', 'manufacturer', 'package_container', 'package_size', 'is_active']
        widgets = {
            'brand_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter brand name'
            }),
            'type': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'dosage_form': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'generic': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter generic name'
            }),
            'strength': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'e.g., 500mg, 10ml'
            }),
            'manufacturer': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter manufacturer name'
            }),
            'package_container': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'e.g., Strip, Bottle, Box'
            }),
            'package_size': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 2,
                'placeholder': 'e.g., 10 tablets per strip'
            }),
        }



