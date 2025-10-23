from django.core.management.base import BaseCommand
from core.models import State, Course

class Command(BaseCommand):
    help = 'Creates basic data for the system including states and courses'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating basic data...')
        
        # Create states
        states = [
            "KWACHANGE",
            "KIFUMBU",
            "ON-CAMPUS (Hostellers)",
            "MAWELA",
            "WHITE HOUSE",
            "MOSHI MJINI"
        ]
        
        # Clear existing states
        State.objects.all().delete()
        
        # Create new states
        state_count = 0
        for state_name in states:
            State.objects.create(name=state_name)
            state_count += 1
        
        self.stdout.write(f'Created {state_count} states')
        
        # Create unique courses from the college data
        courses = [
            ("BsChem", "Bachelor of Science in Chemistry"),
            ("BsCS", "Bachelor of Science in Computer Science"),
            ("BsMathStat", "Bachelor of Science in Mathematics and Statistics"),
            ("BsEd", "Bachelor Science with Education"),
            ("BsBio", "Bachelor of Science in Applied Biology"),
            ("BAccFin", "Bachelor of Accounting and Finance"),
            ("BProcSCM", "Bachelor of Procurement and Supply Chain Management"),
            ("BAProjMgmt", "Bachelor of Arts in Project Planning and Management"),
            ("BABusAdmin", "Bachelor of Arts in Business Administration Management"),
            ("BASW-HR", "Bachelor of Arts in Social Work and Human Rights"),
            ("LLB", "Bachelor of Laws"),
            ("BASocSW", "Bachelor of Arts in Sociology and Social Work"),
            ("BAGeoEnv", "Bachelor of Arts in Geography and Environmental Studies"),
            ("BAEd", "Bachelor of Arts with Education")
        ]
        
        # Clear existing courses
        Course.objects.all().delete()
        
        # Create new courses
        course_count = 0
        for code, name in courses:
            Course.objects.create(code=code, name=name)
            course_count += 1
        
        self.stdout.write(f'Created {course_count} courses')
        
        self.stdout.write(self.style.SUCCESS('Basic data created successfully!'))