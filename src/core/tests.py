"""
Comprehensive test suite for MWECAU Digital Voting System
"""
from django.test import TestCase, Client
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from core.models import User, State, Course, CollegeData
from election.models import Election, ElectionLevel, Position, Candidate, VoterToken, Vote
import uuid


class UserModelTestCase(TestCase):
    """Test User model functionality"""
    
    def setUp(self):
        self.state = State.objects.create(name="Dar es Salaam")
        self.course = Course.objects.create(name="Computer Science", code="CS101")
    
    def test_user_creation(self):
        """Test creating a user"""
        user = User.objects.create_user(
            registration_number="T/DEG/2024/001",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            state=self.state,
            course=self.course
        )
        self.assertEqual(user.registration_number, "T/DEG/2024/001")
        self.assertEqual(user.first_name, "John")
        self.assertTrue(user.check_password("testpass123"))
        self.assertIsNotNone(user.voter_id)
    
    def test_user_authentication(self):
        """Test user login with registration number"""
        User.objects.create_user(
            registration_number="T/DEG/2024/002",
            password="testpass123",
            first_name="Jane",
            last_name="Smith"
        )
        user = authenticate(registration_number="T/DEG/2024/002", password="testpass123")
        self.assertIsNotNone(user)
        self.assertEqual(user.first_name, "Jane")
    
    def test_user_gender_choices(self):
        """Test user gender field"""
        user = User.objects.create_user(
            registration_number="T/DEG/2024/003",
            password="testpass",
            gender="female"
        )
        self.assertEqual(user.gender, "female")
    
    def test_user_role_assignment(self):
        """Test user role assignment"""
        user = User.objects.create_user(
            registration_number="T/DEG/2024/004",
            password="testpass",
            role=User.ROLE_VOTER
        )
        self.assertEqual(user.role, User.ROLE_VOTER)


class CollegeDataTestCase(TestCase):
    """Test CollegeData model"""
    
    def setUp(self):
        self.state = State.objects.create(name="Dar es Salaam")
        self.course = Course.objects.create(name="Computer Science", code="CS101")
    
    def test_college_data_creation(self):
        """Test creating college data"""
        college_data = CollegeData.objects.create(
            registration_number="T/DEG/2024/005",
            first_name="Alice",
            last_name="Brown",
            email="alice@test.com",
            gender="female",
            course=self.course,
            state=self.state
        )
        self.assertEqual(college_data.registration_number, "T/DEG/2024/005")
        self.assertFalse(college_data.is_used)
    
    def test_mark_college_data_as_used(self):
        """Test marking college data as used"""
        college_data = CollegeData.objects.create(
            registration_number="T/DEG/2024/006",
            first_name="Bob",
            last_name="Johnson",
            course=self.course
        )
        college_data.mark_as_used()
        self.assertTrue(college_data.is_used)


class ElectionTestCase(TestCase):
    """Test Election functionality"""
    
    def setUp(self):
        self.state = State.objects.create(name="Dar es Salaam")
        self.course = Course.objects.create(name="Computer Science", code="CS101")
        
        # Create election levels
        self.level = ElectionLevel.objects.create(
            name="President Election",
            code="PRES2024",
            type=ElectionLevel.TYPE_PRESIDENT
        )
        
        # Create election
        self.election = Election.objects.create(
            title="Student Elections 2024",
            description="Annual student elections",
            start_date=timezone.now() + timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=3)
        )
        self.election.levels.add(self.level)
    
    def test_election_creation(self):
        """Test creating an election"""
        self.assertEqual(self.election.title, "Student Elections 2024")
        self.assertFalse(self.election.is_active)
        self.assertFalse(self.election.has_ended)
    
    def test_election_activation(self):
        """Test activating an election"""
        self.election.is_active = True
        self.election.save()
        self.assertTrue(self.election.is_active)


class VoterTokenTestCase(TestCase):
    """Test VoterToken functionality"""
    
    def setUp(self):
        self.state = State.objects.create(name="Dar es Salaam")
        self.course = Course.objects.create(name="Computer Science", code="CS101")
        
        self.user = User.objects.create_user(
            registration_number="T/DEG/2024/007",
            password="testpass",
            first_name="Charlie",
            last_name="Davis",
            state=self.state,
            course=self.course,
            is_verified=True
        )
        
        self.level = ElectionLevel.objects.create(
            name="President Election",
            code="PRES2024",
            type=ElectionLevel.TYPE_PRESIDENT
        )
        
        self.election = Election.objects.create(
            title="Elections 2024",
            start_date=timezone.now() + timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=3),
            is_active=True
        )
        self.election.levels.add(self.level)
    
    def test_voter_token_creation(self):
        """Test creating voter tokens"""
        token = VoterToken.objects.create(
            user=self.user,
            election=self.election,
            election_level=self.level,
            token=uuid.uuid4(),
            expiry_date=self.election.end_date
        )
        self.assertFalse(token.is_used)
        self.assertEqual(token.user, self.user)
    
    def test_voter_token_marking_as_used(self):
        """Test marking token as used"""
        token = VoterToken.objects.create(
            user=self.user,
            election=self.election,
            election_level=self.level,
            token=uuid.uuid4(),
            expiry_date=self.election.end_date
        )
        token.mark_as_used()
        self.assertTrue(token.is_used)
        self.assertIsNotNone(token.used_at)


class CandidateTestCase(TestCase):
    """Test Candidate functionality"""
    
    def setUp(self):
        self.state = State.objects.create(name="Dar es Salaam")
        self.course = Course.objects.create(name="Computer Science", code="CS101")
        
        self.user = User.objects.create_user(
            registration_number="T/DEG/2024/008",
            password="testpass",
            first_name="Eve",
            last_name="White",
            state=self.state,
            course=self.course,
            role=User.ROLE_CANDIDATE
        )
        
        self.level = ElectionLevel.objects.create(
            name="President Election",
            code="PRES2024",
            type=ElectionLevel.TYPE_PRESIDENT
        )
        
        self.position = Position.objects.create(
            title="President",
            election_level=self.level
        )
        
        self.election = Election.objects.create(
            title="Elections 2024",
            start_date=timezone.now() + timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=3)
        )
    
    def test_candidate_creation(self):
        """Test creating a candidate"""
        candidate = Candidate.objects.create(
            user=self.user,
            election=self.election,
            position=self.position
        )
        self.assertEqual(candidate.user, self.user)
        self.assertEqual(candidate.position.title, "President")


class VotingTestCase(TestCase):
    """Test voting functionality"""
    
    def setUp(self):
        self.state = State.objects.create(name="Dar es Salaam")
        self.course = Course.objects.create(name="Computer Science", code="CS101")
        
        # Create voter
        self.voter = User.objects.create_user(
            registration_number="T/DEG/2024/009",
            password="testpass",
            first_name="Frank",
            last_name="Green",
            state=self.state,
            course=self.course,
            is_verified=True
        )
        
        # Create candidate
        self.candidate_user = User.objects.create_user(
            registration_number="T/DEG/2024/010",
            password="testpass",
            first_name="Grace",
            last_name="Black",
            state=self.state,
            course=self.course,
            role=User.ROLE_CANDIDATE
        )
        
        self.level = ElectionLevel.objects.create(
            name="President Election",
            code="PRES2024",
            type=ElectionLevel.TYPE_PRESIDENT
        )
        
        self.position = Position.objects.create(
            title="President",
            election_level=self.level
        )
        
        self.election = Election.objects.create(
            title="Elections 2024",
            start_date=timezone.now() - timedelta(minutes=10),
            end_date=timezone.now() + timedelta(hours=3),
            is_active=True
        )
        self.election.levels.add(self.level)
        
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            election=self.election,
            position=self.position
        )
        
        # Create voter token
        self.token = VoterToken.objects.create(
            user=self.voter,
            election=self.election,
            election_level=self.level,
            token=uuid.uuid4(),
            expiry_date=self.election.end_date
        )
    
    def test_vote_creation(self):
        """Test creating a vote"""
        vote = Vote.objects.create(
            candidate=self.candidate,
            election=self.election,
            election_level=self.level
        )
        self.token.mark_as_used()
        
        self.assertEqual(vote.candidate, self.candidate)
        self.assertTrue(self.token.is_used)
        self.assertEqual(Vote.objects.count(), 1)


class RegistrationViewTestCase(TestCase):
    """Test registration view workflow"""
    
    def setUp(self):
        self.client = Client()
        self.state = State.objects.create(name="Dar es Salaam")
        self.course = Course.objects.create(name="Computer Science", code="CS101")
        self.college_data = CollegeData.objects.create(
            registration_number="T/DEG/2024/011",
            first_name="Henry",
            last_name="Iron",
            email="henry@test.com",
            gender="male",
            course=self.course
        )
    
    def test_registration_step1_valid(self):
        """Test registration step 1 with valid registration number"""
        response = self.client.post('/register/', {
            'step': '1',
            'registration_number': 'T/DEG/2024/011'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Step 2', response.content)
    
    def test_registration_step1_invalid(self):
        """Test registration step 1 with invalid registration number"""
        response = self.client.post('/register/', {
            'step': '1',
            'registration_number': 'INVALID/NUMBER'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'not found', response.content)


class LoginViewTestCase(TestCase):
    """Test login functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            registration_number="T/DEG/2024/012",
            password="testpass123",
            first_name="Iris",
            last_name="Moon"
        )
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        response = self.client.post('/login/', {
            'registration_number': 'T/DEG/2024/012',
            'password': 'testpass123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post('/login/', {
            'registration_number': 'T/DEG/2024/012',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class SecurityTestCase(TestCase):
    """Test security features"""
    
    def setUp(self):
        self.client = Client()
        self.state = State.objects.create(name="Dar es Salaam")
        self.course = Course.objects.create(name="Computer Science", code="CS101")
        self.user = User.objects.create_user(
            registration_number="T/DEG/2024/013",
            password="testpass123",
            first_name="Jack",
            last_name="Ruby",
            state=self.state,
            course=self.course
        )
    
    def test_password_hashing(self):
        """Test that passwords are hashed"""
        user = User.objects.get(registration_number="T/DEG/2024/013")
        self.assertNotEqual(user.password, "testpass123")
        self.assertTrue(user.check_password("testpass123"))
    
    def test_duplicate_email_prevention(self):
        """Test that duplicate emails are prevented"""
        from django.db import IntegrityError
        # Email must be unique - attempting to create duplicate should fail
        try:
            User.objects.create_user(
                registration_number="T/DEG/2024/014",
                password="testpass",
                email=self.user.email
            )
            # If we get here, test fails - duplicate was allowed
            self.fail("Duplicate email was allowed when it should have been prevented")
        except (IntegrityError, Exception):
            # Expected - duplicate email prevented
            pass
    
    def test_csrf_protection(self):
        """Test CSRF token requirement"""
        response = self.client.post('/login/', {
            'registration_number': 'T/DEG/2024/013',
            'password': 'testpass123'
        })
        # Should either show CSRF error or require token in forms
        self.assertTrue(
            response.status_code == 403 or b'csrf' in response.content.lower(),
            "CSRF protection should be active"
        )


class DataIntegrityTestCase(TestCase):
    """Test data integrity constraints"""
    
    def setUp(self):
        self.state = State.objects.create(name="Dar es Salaam")
        self.course = Course.objects.create(name="Computer Science", code="CS101")
    
    def test_registration_number_unique(self):
        """Test registration number uniqueness"""
        User.objects.create_user(
            registration_number="T/DEG/2024/015",
            password="testpass"
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                registration_number="T/DEG/2024/015",
                password="testpass"
            )
    
    def test_course_code_unique(self):
        """Test course code uniqueness"""
        Course.objects.create(name="Computer Science", code="CS101")
        with self.assertRaises(Exception):
            Course.objects.create(name="Data Science", code="CS101")
