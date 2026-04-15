from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('register-shop-owner/', views.register_shop_owner, name='register_shop_owner'),
    path('profile/', views.profile, name='profile'),
    path('register-shop/', views.register_shop, name='register_shop'),
    path('register-shop-with-owner/', views.register_shop_with_owner, name='register_shop_with_owner'),
    path('create-staff/', views.create_staff, name='create_staff'),
]
