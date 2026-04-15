from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from .models import User, Shop


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=20, required=False)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2']


class ShopRegistrationForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'address', 'phone', 'email', 'license_number', 'dgda_license']


class StaffCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2']


class ShopOwnerRegistrationForm(forms.ModelForm):
    """Form for Super Admin to create shop and owner in one go"""
    # Owner fields
    owner_username = forms.CharField(max_length=150)
    owner_email = forms.EmailField()
    owner_first_name = forms.CharField(max_length=150, required=False)
    owner_last_name = forms.CharField(max_length=150, required=False)
    owner_phone = forms.CharField(max_length=20, required=False)
    owner_password1 = forms.CharField(widget=forms.PasswordInput, label='Password')
    owner_password2 = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = Shop
        fields = ['name', 'address', 'phone', 'email', 'license_number', 'dgda_license']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('owner_password1')
        password2 = cleaned_data.get('owner_password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data

    def save(self, commit=True):
        # First save the shop
        shop = super().save(commit=False)
        
        # Create the owner user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        owner = User.objects.create_user(
            username=self.cleaned_data['owner_username'],
            email=self.cleaned_data['owner_email'],
            first_name=self.cleaned_data.get('owner_first_name', ''),
            last_name=self.cleaned_data.get('owner_last_name', ''),
            phone=self.cleaned_data.get('owner_phone', ''),
            password=self.cleaned_data['owner_password1'],
            role=settings.ROLE_SHOP_OWNER,
        )
        
        # Associate the owner with the shop
        shop.save()  # Save shop first to get ID
        owner.shop = shop
        owner.save()
        
        return shop, owner


class ShopOwnerSelfRegistrationForm(UserCreationForm):
    """Form for shop owner to register themselves and create their shop in one go"""
    # Shop fields
    shop_name = forms.CharField(max_length=200, label='Shop Name')
    shop_address = forms.CharField(widget=forms.Textarea, label='Shop Address')
    shop_phone = forms.CharField(max_length=20, label='Shop Phone')
    shop_email = forms.EmailField(label='Shop Email')
    shop_license_number = forms.CharField(max_length=100, label='License Number')
    shop_dgda_license = forms.CharField(max_length=100, required=False, label='DGDA License')
    
    # Owner fields
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=False)
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        # Check if license number already exists
        license_number = cleaned_data.get('shop_license_number')
        if license_number and Shop.objects.filter(license_number=license_number).exists():
            raise forms.ValidationError("A shop with this license number already exists")
        
        return cleaned_data

    def save(self, commit=True):
        # Create the shop first
        shop = Shop.objects.create(
            name=self.cleaned_data['shop_name'],
            address=self.cleaned_data['shop_address'],
            phone=self.cleaned_data['shop_phone'],
            email=self.cleaned_data['shop_email'],
            license_number=self.cleaned_data['shop_license_number'],
            dgda_license=self.cleaned_data.get('shop_dgda_license', ''),
        )
        
        # Create the owner user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        user = super().save(commit=False)
        user.role = settings.ROLE_SHOP_OWNER
        user.shop = shop
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.phone = self.cleaned_data.get('phone', '')
        
        if commit:
            user.save()
        
        return user
