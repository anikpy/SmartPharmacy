from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from core.middleware import role_required
from django.conf import settings


def home(request):
    """Landing page"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'core/home.html')


@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user role"""
    if request.user.role == settings.ROLE_SUPER_ADMIN:
        return redirect('dashboard:super_admin')
    elif request.user.role == settings.ROLE_SHOP_OWNER:
        return redirect('dashboard:shop_owner')
    elif request.user.role == settings.ROLE_SHOP_WORKER:
        return redirect('dashboard:shop_worker')
    else:
        return redirect('core:home')
