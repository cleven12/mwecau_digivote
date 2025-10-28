from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Election
from .tasks import notify_voters_of_active_election

@receiver(pre_save, sender=Election)
def handle_election_activation(sender, instance, **kwargs):
    """
    Signal handler for Election model saves.
    Triggers voter notifications when an election becomes active.
    """
    if not instance.pk:  # Skip for new instances
        return
        
    try:
        old_instance = Election.objects.get(pk=instance.pk)
        # If election is being activated for the first time
        if instance.is_active and not old_instance.is_active:
            # Call notify_voters_of_active_election after the save completes
            # to ensure all election data is up to date
            notify_voters_of_active_election(instance.id)
    except Election.DoesNotExist:
        pass  # Skip for new instances