from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.analytics_dashboard, name='dashboard'),
    path('api/sales-chart/', views.sales_chart_api, name='sales_chart_api'),
    path('api/inventory-chart/', views.inventory_chart_api, name='inventory_chart_api'),
    path('financial-reports/', views.financial_reports, name='financial_reports'),
]
