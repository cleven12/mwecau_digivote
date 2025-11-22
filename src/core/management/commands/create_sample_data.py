"""
Management command to create sample data for testing and development
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User, State, Course, CollegeData
from election.models import Election, ElectionLevel, Position, Candidate, VoterToken
import uuid


class Command(BaseCommand):
    help = 'Create sample data for testing the voting system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Delete existing data before creating sample data',
        )

    def handle(self, *args, **options):
        if options['delete_existing']:
            self.stdout.write("Deleting existing data...")
            User.objects.all().delete()
            State.objects.all().delete()
            Course.objects.all().delete()
            CollegeData.objects.all().delete()
            Election.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("✓ Data deleted"))

        self.stdout.write("Creating sample data...")

        # Create States
        states = []
        state_names = ["Dar es Salaam", "Arusha", "Mbeya", "Dodoma", "Kilimanjaro"]
        for name in state_names:
            state, created = State.objects.get_or_create(name=name)
            states.append(state)
            if created:
                self.stdout.write(f"  ✓ Created state: {name}")

        # Create Courses
        courses = []
        course_data = [
            ("Computer Science", "CS101"),
            ("Information Technology", "IT101"),
            ("Software Engineering", "SE101"),
            ("Business Administration", "BA101"),
            ("Accounting", "ACC101"),
        ]
        for name, code in course_data:
            course, created = Course.objects.get_or_create(name=name, code=code)
            courses.append(course)
            if created:
                self.stdout.write(f"  ✓ Created course: {name} ({code})")

        # Create Election Levels
        level_data = [
            ("President Election", "PRES2024", ElectionLevel.TYPE_PRESIDENT, None, None),
            ("State Leaders", "STATE2024", ElectionLevel.TYPE_STATE, states[0], None),
            ("Course Leaders", "COURSE2024", ElectionLevel.TYPE_COURSE, None, courses[0]),
        ]
        levels = []
        for name, code, level_type, state, course in level_data:
            level, created = ElectionLevel.objects.get_or_create(
                name=name, code=code, type=level_type, defaults={'state': state, 'course': course}
            )
            levels.append(level)
            if created:
                self.stdout.write(f"  ✓ Created election level: {name}")

        # Create Election
        election, created = Election.objects.get_or_create(
            title="MWECAU Student Elections 2024",
            defaults={
                'description': "Annual comprehensive student elections",
                'start_date': timezone.now() + timedelta(hours=2),
                'end_date': timezone.now() + timedelta(hours=6),
                'is_active': False,
            }
        )
        if created:
            for level in levels:
                election.levels.add(level)
            self.stdout.write(f"  ✓ Created election: {election.title}")

        # Create Positions
        position_data = [
            ("President", levels[0]),
            ("Vice President", levels[0]),
            ("State Coordinator", levels[1]),
            ("Course Representative", levels[2]),
        ]
        for title, level in position_data:
            position, created = Position.objects.get_or_create(
                title=title, election_level=level
            )
            if created:
                self.stdout.write(f"  ✓ Created position: {title}")

        # Create Sample Voters
        voter_data = [
            ("T/CS/2024/001", "Alice", "Johnson", "alice@test.com", "female", courses[0], states[0]),
            ("T/CS/2024/002", "Bob", "Smith", "bob@test.com", "male", courses[0], states[0]),
            ("T/IT/2024/001", "Charlie", "Brown", "charlie@test.com", "male", courses[1], states[1]),
            ("T/SE/2024/001", "Diana", "Williams", "diana@test.com", "female", courses[2], states[2]),
            ("T/BA/2024/001", "Edward", "Jones", "edward@test.com", "male", courses[3], states[3]),
        ]

        voters = []
        for reg_num, first, last, email, gender, course, state in voter_data:
            user, created = User.objects.get_or_create(
                registration_number=reg_num,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'email': email,
                    'gender': gender,
                    'course': course,
                    'state': state,
                    'is_verified': True,
                    'role': User.ROLE_VOTER,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                voters.append(user)
                self.stdout.write(f"  ✓ Created voter: {first} {last} ({reg_num})")
            else:
                voters.append(user)

        # Create Sample Candidates
        candidate_data = [
            (voters[0], "President", levels[0]),
            (voters[1], "Vice President", levels[0]),
            (voters[2], "State Coordinator", levels[1]),
        ]

        for user, position_title, level in candidate_data:
            position = Position.objects.get(title=position_title, election_level=level)
            candidate, created = Candidate.objects.get_or_create(
                user=user,
                election=election,
                position=position
            )
            if created:
                self.stdout.write(f"  ✓ Created candidate: {user.get_full_name()} for {position_title}")

        # Create Voter Tokens for all voters
        for voter in voters:
            for level in levels:
                token, created = VoterToken.objects.get_or_create(
                    user=voter,
                    election=election,
                    election_level=level,
                    defaults={
                        'token': uuid.uuid4(),
                        'expiry_date': election.end_date,
                    }
                )
                if created:
                    self.stdout.write(f"  ✓ Created token for {voter.first_name} - {level.name}")

        # Create Commissioner
        commissioner, created = User.objects.get_or_create(
            registration_number="ADMIN/2024/001",
            defaults={
                'first_name': 'Admin',
                'last_name': 'Commissioner',
                'email': 'admin@mwecau.test',
                'is_verified': True,
                'is_staff': True,
                'is_superuser': True,
                'role': User.ROLE_COMMISSIONER,
            }
        )
        if created:
            commissioner.set_password('admin123')
            commissioner.save()
            self.stdout.write(f"  ✓ Created commissioner: {commissioner.get_full_name()}")

        self.stdout.write(self.style.SUCCESS("\n✓ Sample data created successfully!"))
        self.stdout.write("\nSample Login Credentials:")
        self.stdout.write("  Voter: alice@test.com / T/CS/2024/001 / testpass123")
        self.stdout.write("  Admin: admin@mwecau.test / ADMIN/2024/001 / admin123")
        self.stdout.write("\nKey URLs:")
        self.stdout.write("  Home: /")
        self.stdout.write("  Admin Panel: /admin/")
        self.stdout.write("  Commissioner Dashboard: /commissioner/")
