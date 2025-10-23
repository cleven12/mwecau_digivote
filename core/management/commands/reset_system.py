from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Resets the entire system with new data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting system reset...')
        
        self.stdout.write('Updating states...')
        call_command('update_states')
        
        self.stdout.write('Importing college data...')
        call_command('import_college_data')
        
        self.stdout.write('Creating admin user...')
        call_command('create_admin_user')
        
        self.stdout.write('Creating student accounts...')
        call_command('create_student_accounts')
        
        self.stdout.write('Updating election levels and positions...')
        call_command('update_election_levels')
        
        self.stdout.write('Creating a sample election...')
        call_command('create_sample_election')
        
        self.stdout.write(self.style.SUCCESS('System reset complete.'))