from django.core.management.base import BaseCommand
from core.models import User, CollegeData, State
import random

class Command(BaseCommand):
    help = 'Creates student accounts from college data'

    def handle(self, *args, **kwargs):
        # Get all college data
        college_data_entries = CollegeData.objects.all()
        
        # Get all states
        states = list(State.objects.all())
        
        # Standard password for all test accounts
        standard_password = '@2025'
        
        # Track created users
        created_count = 0
        updated_count = 0
        
        for entry in college_data_entries:
            # Use first_name and last_name from the model
            first_name = entry.first_name
            last_name = entry.last_name
            
            # Generate unique email using registration number
            email = f"{entry.registration_number.lower()}@mail.com".replace(' ', '')
            
            # Randomly assign a state
            state = random.choice(states)
            
            try:
                # Check if user already exists
                user = User.objects.get(registration_number=entry.registration_number)
                # Update the user
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.set_password(standard_password)
                user.state = state
                user.course = entry.course
                user.save()
                updated_count += 1
            except User.DoesNotExist:
                # Create a new user
                user = User.objects.create_user(
                    email=email,
                    password=standard_password,
                    first_name=first_name,
                    last_name=last_name,
                    registration_number=entry.registration_number,
                    state=state,
                    course=entry.course,
                    role=User.ROLE_VOTER,
                    is_verified=True
                )
                created_count += 1
                
        self.stdout.write(self.style.SUCCESS(
            f'Created {created_count} new student accounts and updated {updated_count} existing accounts '
            f'with password: {standard_password}'
        ))