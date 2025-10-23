from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = 'Creates the admin user'

    def handle(self, *args, **kwargs):
        # Create admin superuser
        admin_email = 'admin@university.edu'
        admin_password = '@12345678'
        
        try:
            admin = User.objects.get(email=admin_email)
            admin.set_password(admin_password)
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Updated admin user: {admin_email}'))
        except User.DoesNotExist:
            admin = User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
                first_name='Admin',
                last_name='User',
                registration_number='ADMIN-001',
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin_email}'))
            
        # Update commissioner password
        commissioner_email = 'commissioner@university.edu'
        commissioner_password = '@2025'
        
        try:
            commissioner = User.objects.get(email=commissioner_email)
            commissioner.set_password(commissioner_password)
            commissioner.save()
            self.stdout.write(self.style.SUCCESS(f'Updated commissioner password: {commissioner_email}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING(f'Commissioner user not found: {commissioner_email}'))