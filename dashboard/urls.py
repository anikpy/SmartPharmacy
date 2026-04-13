from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('super-admin/', views.super_admin_dashboard, name='super_admin'),
    path('shop-owner/', views.shop_owner_dashboard, name='shop_owner'),
    path('shop-worker/', views.shop_worker_dashboard, name='shop_worker'),
]
