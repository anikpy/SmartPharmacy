from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Public pricing page
    path('pricing/', views.pricing, name='pricing'),
    
    # Subscription management
    path('choose/<slug:plan_slug>/', views.choose_plan, name='choose_plan'),
    path('payment/<int:payment_id>/', views.payment, name='payment'),
    path('my-subscription/', views.my_subscription, name='my_subscription'),
]
