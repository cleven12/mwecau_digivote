from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import Election
from .tasks import notify_voters_of_active_election, schedule_election_reminders


@receiver(pre_save, sender=Election)
def capture_old_election_state(sender, instance, **kwargs):
    """Capture the old state of the election before saving."""
    if not instance.pk:
        return
    try:
        old = Election.objects.get(pk=instance.pk)
        instance._old_is_active = old.is_active
        instance._old_start_date = old.start_date
        instance._old_end_date = old.end_date
    except Election.DoesNotExist:
        instance._old_is_active = None
        instance._old_start_date = None
        instance._old_end_date = None


@receiver(post_save, sender=Election)
def handle_election_activation(sender, instance, created, **kwargs):
    """
    Signal handler for Election model saves.
    Triggers voter notifications and scheduled reminders when an election becomes active.
    """
    if created:
        return  # Don't send notifications for newly created elections
    
    old_active = getattr(instance, '_old_is_active', None)
    
    # If election is being activated for the first time
    if instance.is_active and old_active is False:
        try:
            # Queue the notification task to send tokens to all eligible voters
            notify_voters_of_active_election.delay(instance.id)
            
            # Schedule reminder tasks for this election
            schedule_election_reminders.delay(instance.id)
            
            print(f"Election {instance.id} activated: notifications and reminders queued")
        except Exception as e:
            print(f"Failed to queue election notification/reminders: {e}")
            # Fallback to synchronous calls
            try:
                notify_voters_of_active_election(instance.id)
                schedule_election_reminders(instance.id)
            except Exception as fallback_error:
                print(f"Fallback execution failed: {fallback_error}")
