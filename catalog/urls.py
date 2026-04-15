from django.urls import path
from . import views, api_views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_list, name='list'),
    path('create/', views.catalog_create, name='create'),
    path('<int:pk>/update/', views.catalog_update, name='update'),
    path('<int:pk>/delete/', views.catalog_delete, name='delete'),
    path('custom-medicines/', views.custom_medicines_list, name='custom_medicines_list'),
    path('custom-medicines/<int:pk>/promote/', views.promote_to_master_catalog, name='promote_to_master'),

    # API endpoints
    path('api/search/', api_views.medicine_search_api, name='search_api'),
    path('api/medicine/<int:medicine_id>/', api_views.medicine_details_api, name='medicine_details'),
    path('api/suggestions/', api_views.medicine_search_suggestions, name='suggestions_api'),
]
