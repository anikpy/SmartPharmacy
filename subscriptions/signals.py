from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from users.models import Shop
from .models import Subscription, SubscriptionPlan


@receiver(post_save, sender=Shop)
def create_trial_subscription(sender, instance, created, **kwargs):
    """
    Create a trial subscription when a new shop is registered
    """
    if created:
        try:
            # Get the basic plan for trial
            basic_plan = SubscriptionPlan.objects.filter(plan_type='basic').first()
            
            if basic_plan:
                trial_end = timezone.now() + timedelta(days=14)  # 14-day trial
                
                Subscription.objects.create(
                    shop=instance,
                    plan=basic_plan,
                    status='trial',
                    billing_cycle='monthly',
                    start_date=timezone.now(),
                    end_date=trial_end,
                    trial_end_date=trial_end,
                    current_amount=0,  # Free trial
                    auto_renew=False,
                )
        except Exception as e:
            # Log error but don't break shop creation
            print(f"Error creating trial subscription: {e}")

