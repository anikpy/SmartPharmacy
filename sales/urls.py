from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('pos/', views.pos, name='pos'),
    path('pos/add-item/', views.pos_add_item, name='pos_add_item'),
    path('pos/remove-item/<int:item_id>/', views.pos_remove_item, name='pos_remove_item'),
    path('pos/complete/', views.pos_complete, name='pos_complete'),
    path('transactions/', views.transaction_list, name='list'),
    path('transactions/<int:pk>/', views.transaction_detail, name='detail'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/dues/', views.customer_dues, name='customer_dues'),
    path('customers/<int:pk>/pay-due/', views.pay_due, name='pay_due'),
]
