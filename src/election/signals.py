from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from .models import Election
from .tasks import notify_voters_of_active_election


@receiver(pre_save, sender=Election)
def capture_old_election_state(sender, instance, **kwargs):
    """Capture the old state of the election before saving."""
    if not instance.pk:
        return
    try:
        old = Election.objects.get(pk=instance.pk)
        instance._old_is_active = old.is_active
    except Election.DoesNotExist:
        instance._old_is_active = None


@receiver(post_save, sender=Election)
def handle_election_activation(sender, instance, created, **kwargs):
    """
    Signal handler for Election model saves.
    Triggers voter notifications when an election becomes active.
    """
    if created:
        return  # Don't send notifications for newly created elections
    
    old_active = getattr(instance, '_old_is_active', None)
    
    # If election is being activated for the first time
    if instance.is_active and old_active is False:
        try:
            # Queue the notification task
            notify_voters_of_active_election.delay(instance.id)
        except Exception as e:
            print(f"Failed to queue election notification: {e}")
            # Fallback to synchronous call
            notify_voters_of_active_election(instance.id)