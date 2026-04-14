from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, ShopRegistrationForm, StaffCreationForm
from .models import Shop, User
from core.middleware import role_required
from django.conf import settings


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('core:dashboard')
    else:
        form = UserRegistrationForm()
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
    return render(request, 'users/profile.html', {'user': request.user})


def logout_view(request):
    """Custom logout view that accepts both GET and POST requests"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('users:login')
