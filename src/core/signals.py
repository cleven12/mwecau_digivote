from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User

@receiver(pre_save, sender=User)
def capture_old_state(sender, instance, **kwargs):
    """Capture the old state id before saving so we can compare after save."""
    if not instance.pk:
        return
    try:
        old = User.objects.get(pk=instance.pk)
        instance._old_state_id = old.state_id
    except User.DoesNotExist:
        instance._old_state_id = None


@receiver(post_save, sender=User)
def notify_on_state_change(sender, instance, created, **kwargs):
    """Notify user by email when their `state` field has changed.

    This will run for any save that changes the `state` FK, including admin
    updates or bulk imports. It will not notify on creation or when state is
    unchanged.
    """
    if created:
        return

    old_state = getattr(instance, '_old_state_id', None)
    new_state = instance.state_id

    # If no change, do nothing
    if old_state == new_state:
        return

    # Only notify if user has an email
    if not instance.email:
        return

    # Compose and send email
    subject = "Your account state has been updated"
    message = (
        f"Dear {instance.get_full_name()},\n\n"
        f"Your registered state/region has been updated in the election system.\n"
        f"Previous state id: {old_state}\n"
        f"New state id: {new_state}\n\n"
        "If you did not request this change, please contact support immediately.\n"
        "Regards,\nMWECAU Election Platform"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
            recipient_list=[instance.email],
            fail_silently=False,
        )
    except Exception as e:
        # Avoid raising in signal; just log to stdout for now
        print(f"Failed to send state-change email to {instance.email}: {e}")
