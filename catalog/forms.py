from django import forms
from .models import MasterCatalog


class MasterCatalogForm(forms.ModelForm):
    class Meta:
        model = MasterCatalog
        fields = ['brand_name', 'type', 'dosage_form', 'generic', 'strength', 'manufacturer', 'package_container', 'package_size', 'is_active']
        widgets = {
            'brand_name': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'dosage_form': forms.Select(attrs={'class': 'form-control'}),
            'generic': forms.TextInput(attrs={'class': 'form-control'}),
            'strength': forms.TextInput(attrs={'class': 'form-control'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control'}),
            'package_container': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'package_size': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='Select CSV file',
        help_text='Upload the medicine.csv file with the correct format'
    )
