from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('pos/', views.pos, name='pos'),
    path('pos/add-item/', views.pos_add_item, name='pos_add_item'),
    path('pos/remove-item/<int:item_id>/', views.pos_remove_item, name='pos_remove_item'),
    path('pos/complete/', views.pos_complete, name='pos_complete'),
    path('pos/search-customer/', views.search_customer_by_phone, name='search_customer_by_phone'),
    path('transactions/', views.transaction_list, name='list'),
    path('transactions/<int:pk>/', views.transaction_detail, name='detail'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    path('transactions/customer/<int:customer_id>/history/', views.customer_transaction_history, name='customer_transaction_history'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    path('customers/<int:pk>/dues/', views.customer_dues, name='customer_dues'),
    path('customers/<int:pk>/pay-due/', views.pay_due, name='pay_due'),
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/update/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    path('dashboard/', views.dashboard_analytics, name='dashboard_analytics'),
    path('expiry/', views.expiry_management, name='expiry_management'),
    path('reports/profit-loss/', views.reports_profit_loss, name='reports_profit_loss'),
    path('reports/staff-performance/', views.reports_staff_performance, name='reports_staff_performance'),
    path('reports/tax/', views.reports_tax, name='reports_tax'),
    path('reports/inventory/', views.reports_inventory, name='reports_inventory'),
]
