from rest_framework import permissions
from django.conf import settings


class IsSuperAdmin(permissions.BasePermission):
    """Only Super Admins have access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == settings.ROLE_SUPER_ADMIN


class IsShopOwner(permissions.BasePermission):
    """Only Shop Owners have access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == settings.ROLE_SHOP_OWNER
    
    def has_object_permission(self, request, view, obj):
        # Shop owners can only access their own shop's data
        if hasattr(obj, 'shop'):
            return obj.shop == request.user.shop
        return True


class IsShopWorker(permissions.BasePermission):
    """Only Shop Workers have access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == settings.ROLE_SHOP_WORKER


class IsShopOwnerOrWorker(permissions.BasePermission):
    """Shop Owners and Workers have access"""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role in [settings.ROLE_SHOP_OWNER, settings.ROLE_SHOP_WORKER]
        )
    
    def has_object_permission(self, request, view, obj):
        # Users can only access their own shop's data
        if hasattr(obj, 'shop'):
            return obj.shop == request.user.shop
        return True


class IsShopOwnerOrReadOnly(permissions.BasePermission):
    """Shop Owners can edit, others read-only"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == settings.ROLE_SHOP_OWNER
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'shop'):
            return obj.shop == request.user.shop
        return True
