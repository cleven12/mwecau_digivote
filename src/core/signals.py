from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from .tasks import send_verification_email
import uuid


@receiver(pre_save, sender=User)
def capture_old_verification_state(sender, instance, **kwargs):
    """Capture the old verification status before saving."""
    if not instance.pk:
        return
    try:
        old = User.objects.get(pk=instance.pk)
        instance._old_verified = old.is_verified
        instance._old_state_id = old.state_id
    except User.DoesNotExist:
        instance._old_verified = None
        instance._old_state_id = None


@receiver(post_save, sender=User)
def generate_voter_id_on_create(sender, instance, created, **kwargs):
    """
    Generate voter ID automatically when a user is created.
    This applies to both self-registered and admin-created users.
    """
    if created and not instance.voter_id:
        instance.voter_id = str(uuid.uuid4())
        instance.save(update_fields=['voter_id'])


@receiver(post_save, sender=User)
def generate_tokens_on_verification(sender, instance, created, **kwargs):
    """
    Generate voting tokens and send verification email when a user is verified.
    Triggers both for self-registered users and admin-verified users.
    """
    if created:
        return  # Don't send email on initial creation
    
    old_verified = getattr(instance, '_old_verified', None)
    
    # If user just got verified (transitioned from unverified to verified)
    if not old_verified and instance.is_verified:
        try:
            # Send verification email with tokens for active elections
            send_verification_email.delay(instance.id)
        except Exception as e:
            print(f"Failed to queue verification email for user {instance.id}: {e}")
            # Fallback to synchronous call
            try:
                send_verification_email(instance.id)
            except Exception as fallback_error:
                print(f"Failed to send verification email synchronously: {fallback_error}")


@receiver(post_save, sender=User)
def notify_on_state_change(sender, instance, created, **kwargs):
    """
    Notify user by email when their `state` field has changed.
    This runs for any save that changes the `state` FK, including admin updates or bulk imports.
    It will not notify on creation or when state is unchanged.
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

