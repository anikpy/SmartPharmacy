from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.catalog_list, name='list'),
    path('create/', views.catalog_create, name='create'),
    path('<int:pk>/update/', views.catalog_update, name='update'),
    path('<int:pk>/delete/', views.catalog_delete, name='delete'),
    path('import-csv/', views.import_csv, name='import_csv'),
]
