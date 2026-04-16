from django import forms
from .models import Customer, Transaction, TransactionItem, CustomerDue, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'email', 'address', 'license_number', 'tax_id', 'contact_person', 'notes', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Supplier name'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Email address'}),
            'address': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'rows': 3, 'placeholder': 'Address'}),
            'license_number': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'License number'}),
            'tax_id': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Tax ID'}),
            'contact_person': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Contact person name'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'rows': 3, 'placeholder': 'Additional notes'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-indigo-600 border-2 border-gray-300 rounded focus:ring-indigo-500'}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Enter customer name'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Enter phone number'}),
            'address': forms.Textarea(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'rows': 3, 'placeholder': 'Enter address'}),
        }


class POSItemForm(forms.Form):
    inventory_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1})
    )


class POSForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition'}),
        empty_label="Walk-in Customer"
    )
    search_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Search by phone number'})
    )
    customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Customer Name'})
    )
    customer_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'placeholder': 'Phone'})
    )
    customer_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'rows': 2, 'placeholder': 'Address'})
    )
    payment_method = forms.ChoiceField(
        choices=Transaction.PAYMENT_METHODS,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition'})
    )
    discount_type = forms.ChoiceField(
        choices=[('fixed', 'Fixed Amount'), ('percentage', 'Percentage')],
        initial='percentage',
        widget=forms.Select(attrs={'class': 'flex-1 px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition'})
    )
    discount = forms.DecimalField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'w-32 px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'step': '0.01', 'value': 0, 'placeholder': '0'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition', 'rows': 2, 'placeholder': 'Optional notes'})
    )

    def __init__(self, *args, **kwargs):
        shop = kwargs.pop('shop', None)
        super().__init__(*args, **kwargs)
        if shop:
            self.fields['customer'].queryset = Customer.objects.filter(shop=shop)
