from django.core.management.base import BaseCommand
from core.models import User, CollegeData, State, Course
import csv
import io
import random

class Command(BaseCommand):
    help = 'Creates test users and college data for the system'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating test users and college data...')
        
        # Add admin and commissioner users
        admin_email = 'admin@university.edu'
        admin_password = '@12345678'
        
        try:
            admin = User.objects.get(email=admin_email)
            admin.set_password(admin_password)
            admin.is_staff = True
            admin.is_superuser = True
            admin.save()
            self.stdout.write(f'Updated admin user: {admin_email}')
        except User.DoesNotExist:
            admin = User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
                first_name='Admin',
                last_name='User',
                registration_number='ADMIN-001',
            )
            self.stdout.write(f'Created admin user: {admin_email}')
            
        # Create commissioner
        commissioner_email = 'commissioner@university.edu'
        commissioner_password = '@2025'
        
        try:
            commissioner = User.objects.get(email=commissioner_email)
            self.stdout.write(f'Admin user {commissioner_email} already exists')
            commissioner.set_password(commissioner_password)
            commissioner.role = User.ROLE_COMMISSIONER
            commissioner.is_staff = True
            commissioner.save()
        except User.DoesNotExist:
            User.objects.create_user(
                email=commissioner_email,
                password=commissioner_password,
                first_name='Election',
                last_name='Commissioner',
                registration_number='COMM-001',
                role=User.ROLE_COMMISSIONER,
                is_staff=True,
                is_verified=True
            )
            self.stdout.write(f'Created commissioner user: {commissioner_email}')
        
        # Create class leader
        class_leader_email = 'classleader@university.edu'
        class_leader_password = '@2025'
        
        try:
            class_leader = User.objects.get(email=class_leader_email)
            self.stdout.write(f'Class leader {class_leader_email} already exists')
            class_leader.set_password(class_leader_password)
            class_leader.role = User.ROLE_CLASS_LEADER
            class_leader.save()
        except User.DoesNotExist:
            User.objects.create_user(
                email=class_leader_email,
                password=class_leader_password,
                first_name='Class',
                last_name='Leader',
                registration_number='CL-001',
                role=User.ROLE_CLASS_LEADER,
                is_verified=True
            )
            self.stdout.write(f'Created class leader: {class_leader_email}')
        
        # Add the CSV data for college data
        csv_data = """registration_number, full_name, course_code, course_name
REG-001, Paul Mbise, BsChem, Bachelor of Science in Chemistry
REG-002, Neema Mwijage, BsCS, Bachelor of Science in Computer Science
REG-003, George Mkenda, BsMathStat, Bachelor of Science in Mathematics and Statistics
REG-004, Victor Ndege, BsEd, Bachelor Science with Education
REG-005, Francis Mtitu, BsBio, Bachelor of Science in Applied Biology
REG-006, Anyes Mushi, BAccFin, Bachelor of Accounting and Finance
REG-007, Laureen Sanga, BProcSCM, Bachelor of Procurement and Supply Chain Management
REG-008, Jesca Nyanda, BAProjMgmt, Bachelor of Arts in Project Planning and Management
REG-009, Faustine Mwita, BABusAdmin, Bachelor of Arts in Business Administration Management
REG-010, Cleven Komba, BASW-HR, Bachelor of Arts in Social Work and Human Rights
REG-011, Anna Mwaya, LLB, Bachelor of Laws
REG-012, Evenlight Kabwe, BASocSW, Bachelor of Arts in Sociology and Social Work
REG-013, Glory Nguma, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
REG-014, Nehemia Bakari, BAEd, Bachelor of Arts with Education
REG-015, Nyanda Nkwabi, BsChem, Bachelor of Science in Chemistry
REG-016, Massawe Mwandu, BsCS, Bachelor of Science in Computer Science
REG-017, Debora Mbezi, BsMathStat, Bachelor of Science in Mathematics and Statistics
REG-018, Obeni Chitende, BsEd, Bachelor Science with Education
REG-019, Jackson Nguvumali, BsBio, Bachelor of Science in Applied Biology
REG-020, Levina Mwingira, BAccFin, Bachelor of Accounting and Finance
REG-021, Loveness Mdoe, BProcSCM, Bachelor of Procurement and Supply Chain Management
REG-022, Benson Samia, BAProjMgmt, Bachelor of Arts in Project Planning and Management
REG-023, Samia Othman, BABusAdmin, Bachelor of Arts in Business Administration Management
REG-024, Cleophas Mrema, BASW-HR, Bachelor of Arts in Social Work and Human Rights
REG-025, Esther Mwakatobe, LLB, Bachelor of Laws
REG-026, Gloria Mwinuka, BASocSW, Bachelor of Arts in Sociology and Social Work
REG-027, Nyota Mwita, BAGeoEnv, Bachelor of Arts in Geography and Environmental Studies
REG-028, Neema Abas, BAEd, Bachelor of Arts with Education
REG-029, Victor Ndago, BsChem, Bachelor of Science in Chemistry
REG-030, George Mwinyi, BsCS, Bachelor of Science in Computer Science"""

        # Clear existing college data
        CollegeData.objects.all().delete()
        
        # Process the CSV data
        csv_file = io.StringIO(csv_data)
        reader = csv.reader(csv_file, delimiter=',')
        next(reader)  # Skip header row
        
        # Get all courses
        courses = {course.code: course for course in Course.objects.all()}
        
        # Create college data entries
        college_data_count = 0
        for row in reader:
            registration_number = row[0].strip()
            full_name = row[1].strip()
            course_code = row[2].strip()
            
            if course_code in courses:
                course = courses[course_code]
                
                CollegeData.objects.create(
                    registration_number=registration_number,
                    full_name=full_name,
                    course=course
                )
                college_data_count += 1
        
        self.stdout.write(f'Created {college_data_count} college data entries')
        
        # Get all states
        states = list(State.objects.all())
        
        # Create student accounts from college data
        standard_password = '@2025'
        test_users_count = 0
        
        for entry in CollegeData.objects.all():
            # Generate email from name
            name_parts = entry.full_name.split()
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            email = f"{first_name.lower()}.{last_name.lower()}@university.edu".replace(' ', '')
            
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
                user.is_verified = True
                user.save()
            except User.DoesNotExist:
                # Create a new user
                voter_id = f"V{random.randint(10000, 99999)}"
                
                user = User.objects.create_user(
                    email=email,
                    password=standard_password,
                    first_name=first_name,
                    last_name=last_name,
                    registration_number=entry.registration_number,
                    voter_id=voter_id,
                    state=state,
                    course=entry.course,
                    role=User.ROLE_VOTER,
                    is_verified=True
                )
                test_users_count += 1
        
        self.stdout.write(f'Created {test_users_count} test users')
        
        # Create some candidates
        from election.models import Election, Position, Candidate, Vote
        
        # Get the active election
        try:
            active_election = Election.objects.filter(is_active=True, has_ended=False).first()
            if active_election:
                # Get all positions
                positions = Position.objects.all()
                
                # Get all users who can be candidates (voters)
                potential_candidates = User.objects.filter(role=User.ROLE_VOTER)
                
                # Create candidates for each position
                candidate_count = 0
                for position in positions:
                    # Filter potential candidates based on position criteria
                    eligible_candidates = potential_candidates
                    
                    if position.gender_restriction != Position.GENDER_ANY:
                        # We don't have gender field in User, so we'll skip this filter for now
                        pass
                        
                    if position.state:
                        eligible_candidates = eligible_candidates.filter(state=position.state)
                        
                    if position.course:
                        eligible_candidates = eligible_candidates.filter(course=position.course)
                    
                    # Get list of eligible candidates
                    eligible_candidates = list(eligible_candidates)
                    
                    # Create 1-3 candidates for this position if there are eligible candidates
                    if eligible_candidates:
                        # Determine number of candidates for this position
                        num_candidates = min(len(eligible_candidates), random.randint(1, 3))
                        
                        # Randomly select candidates
                        for i in range(num_candidates):
                            if eligible_candidates:
                                candidate_user = random.choice(eligible_candidates)
                                eligible_candidates.remove(candidate_user)
                                
                                # Set user as candidate
                                candidate_user.role = User.ROLE_CANDIDATE
                                candidate_user.save()
                                
                                # Create candidate record
                                try:
                                    Candidate.objects.create(
                                        user=candidate_user,
                                        election=active_election,
                                        position=position,
                                        bio=f"Campaign bio for {candidate_user.first_name}",
                                        platform=f"Election platform for {candidate_user.first_name}"
                                    )
                                    candidate_count += 1
                                except:
                                    # Skip if candidate already exists
                                    pass
                
                self.stdout.write(f'Created {candidate_count} candidates')
                
                # Create some random votes
                # Get all candidates
                candidates = Candidate.objects.filter(election=active_election)
                
                # Get all voters
                voters = User.objects.filter(role__in=[User.ROLE_VOTER, User.ROLE_CANDIDATE])
                
                # Create random votes
                vote_count = 0
                for voter in voters:
                    # Find positions this voter can vote for
                    eligible_positions = []
                    
                    for position in positions:
                        if position.election_level.code == 'president':
                            # All voters can vote for president
                            eligible_positions.append(position)
                        elif position.election_level.code == 'state' and position.state == voter.state:
                            # Voters can vote for their state's positions
                            eligible_positions.append(position)
                        elif position.election_level.code == 'course' and position.course == voter.course:
                            # Voters can vote for their course's positions
                            eligible_positions.append(position)
                    
                    # For each eligible position, vote for a random candidate
                    for position in eligible_positions:
                        # Get candidates for this position
                        position_candidates = candidates.filter(position=position)
                        
                        if position_candidates:
                            # Choose a random candidate
                            random_candidate = random.choice(position_candidates)
                            
                            # Create vote
                            try:
                                Vote.objects.create(
                                    voter=voter,
                                    candidate=random_candidate
                                )
                                vote_count += 1
                            except:
                                # Skip if vote already exists
                                pass
                
                self.stdout.write(f'Created {vote_count} random votes')
            else:
                self.stdout.write('No active election found for creating candidates and votes')
        except Exception as e:
            self.stdout.write(f'Error creating candidates and votes: {str(e)}')
        
        self.stdout.write(self.style.SUCCESS('Test data creation completed'))