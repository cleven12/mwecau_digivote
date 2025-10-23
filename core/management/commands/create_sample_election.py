from django.core.management.base import BaseCommand
from election.models import Election, ElectionLevel
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Creates a sample election with all election levels linked'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        
        # Get all election levels
        election_levels = ElectionLevel.objects.all()
        
        if not election_levels.exists():
            self.stdout.write(self.style.ERROR(
                'No election levels found! Run "python manage.py create_elections" first.'
            ))
            return
        
        # Create an ongoing election (started yesterday, ends in 6 days)
        ongoing_election, created = Election.objects.get_or_create(
            title='University Elections 2025',
            defaults={
                'description': 'Annual university elections for selecting student representatives at all levels.',
                'start_date': now - timedelta(days=1),
                'end_date': now + timedelta(days=6),
                'is_active': True,
                'has_ended': False
            }
        )
        
        # Link all election levels to this election
        ongoing_election.levels.set(election_levels)
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Created ongoing election: {ongoing_election.title}'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Election already exists: {ongoing_election.title}'
            ))
        
        # Display election details
        self.stdout.write(f'\n📋 Election Details:')
        self.stdout.write(f'   Title: {ongoing_election.title}')
        self.stdout.write(f'   Start: {ongoing_election.start_date}')
        self.stdout.write(f'   End: {ongoing_election.end_date}')
        self.stdout.write(f'   Status: {"🟢 ACTIVE" if ongoing_election.is_active else "🔴 INACTIVE"}')
        self.stdout.write(f'   Levels: {ongoing_election.levels.count()} levels linked')
        
        # Show breakdown by level type
        president_count = ongoing_election.levels.filter(type=ElectionLevel.TYPE_PRESIDENT).count()
        state_count = ongoing_election.levels.filter(type=ElectionLevel.TYPE_STATE).count()
        course_count = ongoing_election.levels.filter(type=ElectionLevel.TYPE_COURSE).count()
        
        self.stdout.write(f'\n🗳️  Election Level Breakdown:')
        self.stdout.write(f'   President Levels: {president_count}')
        self.stdout.write(f'   State Levels: {state_count}')
        self.stdout.write(f'   Course Levels: {course_count}')
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Sample election setup complete!'
        ))
