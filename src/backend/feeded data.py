from core.models import User, CollegeData, Course, State
commissioner = User.objects.create_superuser(registration_number='T/ADMIN/2020/001', email='admin@example.com', password='adminpass')
state = State.objects.create(name='Change State')
course = Course.objects.create(name='Computer Science', code='CS101')
CollegeData.objects.create(registration_number='T/XXX/2020/002', first_name='John', last_name='Doe', email='john@university.com', course=course, uploaded_by=commissioner)