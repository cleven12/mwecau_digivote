from django.core.management.base import BaseCommand
from election.models import ElectionLevel, Position
from core.models import State, Course


class Command(BaseCommand):
    help = 'Creates election levels and positions based on database models'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating election levels and positions...')
        
        # ===== 1. PRESIDENT LEVEL =====
        president_level, created = ElectionLevel.objects.get_or_create(
            code='PRES-2025',
            defaults={
                'name': 'University President',
                'type': ElectionLevel.TYPE_PRESIDENT,
                'description': 'University-wide presidential election. Open to all students.'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created President level: {president_level.name}'))
        
        # Create president position
        Position.objects.get_or_create(
            title='University President',
            election_level=president_level,
            gender_restriction=Position.GENDER_ANY,
            defaults={
                'description': 'President of the university student body. Represents all students.'
            }
        )
        
        # ===== 2. STATE LEVELS =====
        states = State.objects.all()
        state_levels_created = 0
        state_positions_created = 0
        
        for state in states:
            # Create a state-specific election level
            state_level, created = ElectionLevel.objects.get_or_create(
                code=f'STATE-{state.name.upper().replace(" ", "-")}-2025',
                defaults={
                    'name': f'{state.name} State Leader',
                    'type': ElectionLevel.TYPE_STATE,
                    'state': state,
                    'description': f'State leader election for {state.name}. Only students from {state.name} can vote.'
                }
            )
            if created:
                state_levels_created += 1
            
            # Create male position for this state level
            Position.objects.get_or_create(
                title='Male State Leader',
                election_level=state_level,
                gender_restriction=Position.GENDER_MALE,
                defaults={
                    'description': f'Male representative for {state.name} state.'
                }
            )
            state_positions_created += 1
            
            # Create female position for this state level
            Position.objects.get_or_create(
                title='Female State Leader',
                election_level=state_level,
                gender_restriction=Position.GENDER_FEMALE,
                defaults={
                    'description': f'Female representative for {state.name} state.'
                }
            )
            state_positions_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Created {state_levels_created} state levels and {state_positions_created} state positions'
        ))
        
        # ===== 3. COURSE LEVELS =====
        courses = Course.objects.all()
        course_levels_created = 0
        course_positions_created = 0
        
        for course in courses:
            # Create a course-specific election level
            course_level, created = ElectionLevel.objects.get_or_create(
                code=f'COURSE-{course.code.upper()}-2025',
                defaults={
                    'name': f'{course.name} Course Leader',
                    'type': ElectionLevel.TYPE_COURSE,
                    'course': course,
                    'description': f'Course leader election for {course.name}. Only students from {course.code} can vote.'
                }
            )
            if created:
                course_levels_created += 1
            
            # Create male position for this course level
            Position.objects.get_or_create(
                title='Male Course Leader',
                election_level=course_level,
                gender_restriction=Position.GENDER_MALE,
                defaults={
                    'description': f'Male representative for {course.name} course.'
                }
            )
            course_positions_created += 1
            
            # Create female position for this course level
            Position.objects.get_or_create(
                title='Female Course Leader',
                election_level=course_level,
                gender_restriction=Position.GENDER_FEMALE,
                defaults={
                    'description': f'Female representative for {course.name} course.'
                }
            )
            course_positions_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Created {course_levels_created} course levels and {course_positions_created} course positions'
        ))
        
        # Summary
        total_levels = ElectionLevel.objects.count()
        total_positions = Position.objects.count()
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Elections setup complete!'
        ))
        self.stdout.write(f'  Total Election Levels: {total_levels}')
        self.stdout.write(f'  Total Positions: {total_positions}')
