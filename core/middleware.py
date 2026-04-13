from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve


class RoleBasedAccessMiddleware:
    """
    Middleware to enforce role-based access control.
    Uses view-level role decorators as the primary mechanism,
    with this middleware as a fallback for additional checks.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Skip middleware for login/logout pages
        if request.path in ['/accounts/login/', '/accounts/logout/', '/users/login/', '/users/logout/']:
            return self.get_response(request)
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Allow access to login page
            if request.path != '/users/login/':
                return redirect('users:login')
        
        response = self.get_response(request)
        return response


def role_required(*allowed_roles):
    """
    Decorator to restrict view access based on user roles.
    Usage:
        @role_required('SUPER_ADMIN', 'SHOP_OWNER')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('users:login')
            
            if request.user.role not in allowed_roles:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('core:dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def shop_required(view_func):
    """
    Decorator to ensure user has a shop assigned.
    Used for SHOP_OWNER and SHOP_WORKER roles.
    """
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        
        if request.user.role in [settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER]:
            if not request.user.shop:
                messages.error(request, "No shop assigned to your account.")
                return redirect('core:dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
