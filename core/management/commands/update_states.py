from django.core.management.base import BaseCommand
from core.models import State

class Command(BaseCommand):
    help = 'Updates the states in the database'

    def handle(self, *args, **kwargs):
        # Remove existing states
        State.objects.all().delete()
        
        # Create new states
        states = [
            "KWACHANGE",
            "KIFUMBU",
            "ON-CAMPUS (Hostellers)",
            "MAWELA",
            "WHITE HOUSE",
            "MOSHI MJINI"
        ]
        
        state_count = 0
        for state_name in states:
            State.objects.create(name=state_name)
            state_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {state_count} states'))