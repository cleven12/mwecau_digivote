from django.core.management.base import BaseCommand
from election.models import ElectionLevel, Position
from core.models import State, Course

class Command(BaseCommand):
    help = 'Sets up election levels and positions according to requirements'

    def handle(self, *args, **kwargs):
        # Clear existing election levels
        ElectionLevel.objects.all().delete()
        
        # Create the three required election levels
        president_level = ElectionLevel.objects.create(
            name='University President',
            code='president',
            description='University-wide presidential election. Open to all students.'
        )
        
        state_level = ElectionLevel.objects.create(
            name='State Leader',
            code='state',
            description='Elections for state representatives. Students can only vote for candidates from their state.'
        )
        
        course_level = ElectionLevel.objects.create(
            name='Course Leader',
            code='course',
            description='Elections for course representatives. Students can only vote for candidates from their course.'
        )
        
        self.stdout.write(self.style.SUCCESS('Created election levels: University President, State Leader, Course Leader'))
        
        # Clear existing positions
        Position.objects.all().delete()
        
        # Create university president position
        Position.objects.create(
            title='University President',
            election_level=president_level,
            description='President of the university student body. Represents all students.',
            gender_restriction='any'
        )
        
        # Create state leader positions (male and female for each state)
        states = State.objects.all()
        state_position_count = 0
        
        for state in states:
            Position.objects.create(
                title='Male State Leader',
                election_level=state_level,
                description=f'Male representative for {state.name} state.',
                gender_restriction='male',
                state=state
            )
            
            Position.objects.create(
                title='Female State Leader',
                election_level=state_level,
                description=f'Female representative for {state.name} state.',
                gender_restriction='female',
                state=state
            )
            
            state_position_count += 2
        
        # Create course leader positions (male and female for each course)
        courses = Course.objects.all()
        course_position_count = 0
        
        for course in courses:
            Position.objects.create(
                title='Male Course Leader',
                election_level=course_level,
                description=f'Male representative for {course.name} course.',
                gender_restriction='male',
                course=course
            )
            
            Position.objects.create(
                title='Female Course Leader',
                election_level=course_level,
                description=f'Female representative for {course.name} course.',
                gender_restriction='female',
                course=course
            )
            
            course_position_count += 2
        
        self.stdout.write(self.style.SUCCESS(
            f'Created 1 university president position, {state_position_count} state leader positions, '
            f'and {course_position_count} course leader positions'
        ))