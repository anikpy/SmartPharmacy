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
    path('api/search-catalog/', views.search_master_catalog, name='search_catalog'),
    path('add-custom/', views.add_custom_medicine, name='add_custom'),
    path('my-customs/', views.my_custom_medicines, name='my_customs'),
    path('custom-inventory/add/', views.custom_inventory_add, name='custom_inventory_add'),
    path('custom-inventory/', views.custom_inventory_list, name='custom_inventory_list'),
    path('custom-inventory/<int:pk>/update/', views.custom_inventory_update, name='custom_inventory_update'),
    path('custom-inventory/<int:pk>/delete/', views.custom_inventory_delete, name='custom_inventory_delete'),
]
