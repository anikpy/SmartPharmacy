from django import forms
from .models import ShopInventory
from catalog.models import MasterCatalog


class ShopInventoryForm(forms.ModelForm):
    class Meta:
        model = ShopInventory
        fields = ['master_medicine', 'local_price', 'stock_quantity', 'expiry_date', 'batch_number', 'low_stock_threshold', 'is_active']
        widgets = {
            'master_medicine': forms.Select(attrs={'class': 'form-control'}),
            'local_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AddToInventoryForm(forms.Form):
    """Form to add medicine from master catalog to shop inventory"""
    master_medicine = forms.ModelChoiceField(
        queryset=MasterCatalog.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Select Medicine'
    )
    local_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Local Price'
    )
    stock_quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Stock Quantity'
    )
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Expiry Date'
    )
    batch_number = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Batch Number'
    )
