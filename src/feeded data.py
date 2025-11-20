from core.models import User, CollegeData, Course, State

# Create superuser
commissioner, _ = User.objects.get_or_create(registration_number='T/ADMIN/2020/0002',email='admin@mail.com',defaults={'password': '123', 'is_superuser': True, 'is_staff': True})
commissioner.set_password('123')
commissioner.save()

# Create State and Course
state, _ = State.objects.get_or_create(name='Kifumbu')
course, _ = Course.objects.get_or_create(name='Computer Science', code='BsCS')

# Update CollegeData
college_data, _ = CollegeData.objects.get_or_create(registration_number='T/DEG/2020/0003',defaults={'first_name': 'Neema','last_name': 'John','email': 'neema@mail.com','course': course,'uploaded_by': commissioner})
college_data.first_name = 'Neema'
college_data.last_name = 'John'
college_data.email = 'neema@mail.com'
college_data.course = course
college_data.uploaded_by = commissioner
college_data.is_used = False  # Ensure it’s not marked as used
college_data.save()


# from core.models import User, CollegeData, Course, State
# from election.models import Election

# # Create superuser (commissioner)
# commissioner = User.objects.create_superuser(
#     registration_number='T/ADMIN/2020/0002',
#     email='admin@mail.com',
#     password='adminpass'
# )

# # Create State and Course
# state = State.objects.create(name='Kifumbu')
# course = Course.objects.create(name='Computer Science', code='CS100')

# # Create CollegeData
# CollegeData.objects.create(
#     registration_number='T/DEG/2020/0003',
#     first_name='Neema',
#     last_name='John',
#     email='neema@mail.com',
#     course=course,
#     uploaded_by=commissioner
# )

# # Create an active election (for voter tokens)
# Election.objects.create(
#     title='Student Election 2025',
#     start_date='2025-08-01',
#     end_date='2025-08-30',
#     is_active=True,
#     has_ended=False
# )