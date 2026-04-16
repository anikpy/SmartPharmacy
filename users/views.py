from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (
    UserRegistrationForm, 
    ShopRegistrationForm, 
    StaffCreationForm,
    ShopOwnerRegistrationForm,
    ShopOwnerSelfRegistrationForm,
)
from .models import Shop, User
from core.middleware import role_required
from django.conf import settings


def register(request):
    """User registration with optional shop creation for Shop Owners"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        
        if form.is_valid():
            # Get the role from the form (now properly submitted)
            role = form.cleaned_data.get('role', settings.ROLE_SHOP_OWNER)
            is_shop_owner = (role == settings.ROLE_SHOP_OWNER)
            
            # Handle shop creation for shop owners
            if is_shop_owner:
                # Check if shop details are provided
                shop_name = request.POST.get('shop_name', '').strip()
                shop_license_number = request.POST.get('shop_license_number', '').strip()
                shop_address = request.POST.get('shop_address', '').strip()
                shop_phone = request.POST.get('shop_phone', '').strip()
                shop_email = request.POST.get('shop_email', '').strip()
                
                # Validate required shop fields
                errors = []
                if not shop_name:
                    errors.append('Shop name is required')
                if not shop_license_number:
                    errors.append('License number is required')
                if not shop_address:
                    errors.append('Shop address is required')
                if not shop_phone:
                    errors.append('Shop phone is required')
                if not shop_email:
                    errors.append('Shop email is required')
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                    # Return form for correction
                    return render(request, 'users/register.html', {'form': form})
                
                try:
                    # Create the shop
                    shop = Shop.objects.create(
                        name=shop_name,
                        address=shop_address,
                        phone=shop_phone,
                        email=shop_email,
                        license_number=shop_license_number,
                        dgda_license=request.POST.get('shop_dgda_license', '').strip(),
                    )
                    
                    # Create user and associate with shop
                    user = form.save(commit=False)
                    user.role = settings.ROLE_SHOP_OWNER
                    user.shop = shop
                    user.save()
                    
                    messages.success(request, f'Registration successful! Your shop "{shop.name}" has been created.')
                    login(request, user)
                    return redirect('core:dashboard')
                except Exception as e:
                    messages.error(request, f'Error creating shop: {str(e)}')
                    return render(request, 'users/register.html', {'form': form})
            else:
                # Regular registration
                user = form.save(commit=False)
                user.role = role
                user.save()
                
                messages.success(request, 'Registration successful!')
                login(request, user)
                return redirect('core:dashboard')
        else:
            # Form has errors - will be displayed in template
            pass
    else:
        form = UserRegistrationForm()
        # Pre-select SHOP_OWNER as default
        form.initial['role'] = settings.ROLE_SHOP_OWNER
    
    return render(request, 'users/register.html', {'form': form})


@login_required
@role_required(settings.ROLE_SUPER_ADMIN)
def register_shop(request):
    """Super Admin can register new shops"""
    if request.method == 'POST':
        form = ShopRegistrationForm(request.POST)
        if form.is_valid():
            shop = form.save()
            messages.success(request, f'Shop {shop.name} registered successfully!')
            return redirect('dashboard:super_admin')
    else:
        form = ShopRegistrationForm()
    return render(request, 'users/register_shop.html', {'form': form})


@login_required
@role_required(settings.ROLE_SUPER_ADMIN)
def register_shop_with_owner(request):
    """Super Admin can register new shop with owner in one form"""
    if request.method == 'POST':
        form = ShopOwnerRegistrationForm(request.POST)
        if form.is_valid():
            shop, owner = form.save()
            messages.success(request, f'Shop "{shop.name}" and owner "{owner.username}" created successfully!')
            return redirect('dashboard:super_admin')
    else:
        form = ShopOwnerRegistrationForm()
    return render(request, 'users/register_shop_with_owner.html', {'form': form})


@login_required
@role_required(settings.ROLE_SUPER_ADMIN)
def delete_shop(request, pk):
    """Super Admin can delete a shop (soft delete)"""
    from .models import Shop
    shop = get_object_or_404(Shop, pk=pk)

    if request.method == 'POST':
        shop_name = shop.name
        # Soft delete - set is_active to False instead of deleting
        shop.is_active = False
        shop.save()
        # Also deactivate all users associated with this shop
        shop.staff.update(is_active=False)
        messages.success(request, f'Shop "{shop_name}" deactivated successfully!')
        return redirect('dashboard:super_admin')

    return render(request, 'users/shop_confirm_delete.html', {'shop': shop})


def register_shop_owner(request):
    """Public registration for shop owners to create their shop"""
    if request.method == 'POST':
        form = ShopOwnerSelfRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Your shop has been created.')
            return redirect('core:dashboard')
    else:
        form = ShopOwnerSelfRegistrationForm()
    return render(request, 'users/register_shop_owner.html', {'form': form})


@login_required
@role_required(settings.ROLE_SHOP_OWNER)
def create_staff(request):
    """Shop Owner can create staff accounts"""
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            staff = form.save(commit=False)
            staff.role = settings.ROLE_SHOP_WORKER
            staff.shop = request.user.shop
            staff.save()
            messages.success(request, f'Staff {staff.username} created successfully!')
            return redirect('dashboard:shop_owner')
    else:
        form = StaffCreationForm()
    return render(request, 'users/create_staff.html', {'form': form})


@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        # Update user fields
        user = request.user
        user.email = request.POST.get('email', '')
        user.phone = request.POST.get('phone', '')
        user.save()

        # Update shop fields if user has a shop
        if user.shop:
            shop = user.shop
            shop.name = request.POST.get('shop_name', shop.name)
            shop.phone = request.POST.get('shop_phone', shop.phone)
            shop.email = request.POST.get('shop_email', shop.email)
            shop.license_number = request.POST.get('shop_license', shop.license_number)
            shop.address = request.POST.get('shop_address', shop.address)
            shop.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')

    return render(request, 'users/profile.html', {'user': request.user})


def logout_view(request):
    """Custom logout view that accepts both GET and POST requests"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('core:home')
