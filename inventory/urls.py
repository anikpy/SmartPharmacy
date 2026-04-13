from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_list, name='list'),
    path('add/', views.inventory_add, name='add'),
    path('<int:pk>/update/', views.inventory_update, name='update'),
    path('<int:pk>/delete/', views.inventory_delete, name='delete'),
    path('low-stock/', views.low_stock_alerts, name='low_stock'),
    path('search/', views.search_medicines, name='search'),
]
