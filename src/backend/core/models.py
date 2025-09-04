from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
import secrets
import uuid

class UserManager(BaseUserManager):
    """Define a model manager for User model with registration number authentication."""

    use_in_migrations = True

    def _create_user(self, registration_number, password, **extra_fields):
        """Create and save a User with the given registration number and password."""
        if not registration_number:
            raise ValueError('The given registration number must be set')
        
        # Normalize email
        email = extra_fields.get('email')
        if email:
            extra_fields['email'] = self.normalize_email(email)
            
        user = self.model(registration_number=registration_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, registration_number, password=None, **extra_fields):
        """Create and save a regular User with the given registration number."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(registration_number, password, **extra_fields)

    def create_superuser(self, registration_number, password, **extra_fields):
        """Create and save a SuperUser with the given registration number."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(registration_number, password, **extra_fields)

    # ---- CORRECTION: Ensure this method starts at the same indentation level as other methods ----
    def create_from_college_data(self, college_data_id):
        """Create a User from CollegeData, generating a secure voter_id and password.
        Uses email from CollegeData if available and valid, otherwise defers email setting.
        Modified to use UUID for voter_id.
        """
        from .models import CollegeData
        college_data = CollegeData.objects.get(id=college_data_id)
        if college_data.is_used:
            raise ValueError('College data already used')

        # Generate random password and voter_id
        default_password = secrets.token_hex(8)
        voter_id = str(uuid.uuid4())  # Use UUID for secure, unique voter_id

        # Prepare user creation arguments
        user_creation_kwargs = {
            'registration_number': college_data.registration_number,
            'password': default_password,
            'first_name': college_data.first_name,
            'last_name': college_data.last_name,
            'course': college_data.course,
            'voter_id': voter_id,
            'is_verified': False
        }

        # Only pass email if it's present and not just whitespace in CollegeData
        # This prevents passing '' which causes the unique constraint error
        # Check if college_data.email exists and is not just whitespace
        college_data_email = getattr(college_data, 'email', None) # Safer way to get attribute
        if college_data_email and college_data_email.strip():
            user_creation_kwargs['email'] = college_data_email.strip() # Use stripped email

        # Create user with prepared arguments
        user = self.create_user(**user_creation_kwargs)

        college_data.mark_as_used()
        return user, default_password
    # ---- END CORRECTION ----

    def generate_voter_token(self, user_id, election_id):
        """Generate a VoterToken for a user and election."""
        from election.models import VoterToken, Election
        user = self.get(id=user_id)
        if not user.can_vote():
            raise ValueError('User is not eligible to vote')
        
        election = Election.objects.get(id=election_id)
        if not election.is_ongoing():
            raise ValueError('Election is not ongoing')
        
        token, created = VoterToken.objects.get_or_create(
            user=user,
            election=election,
            defaults={'token': uuid.uuid4()}
        )
        if not created and token.is_used:
            raise ValueError('Voter token already used')
        
        return token


# V[01]
# class UserManager(BaseUserManager):
#     """Define a model manager for User model with registration number authentication."""

#     use_in_migrations = True

#     def _create_user(self, registration_number, password, **extra_fields):
#         """Create and save a User with the given registration number and password."""
#         if not registration_number:
#             raise ValueError('The given registration number must be set')
        
#         # Normalize email
#         email = extra_fields.get('email')
#         if email:
#             extra_fields['email'] = self.normalize_email(email)
            
#         user = self.model(registration_number=registration_number, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_user(self, registration_number, password=None, **extra_fields):
#         """Create and save a regular User with the given registration number."""
#         extra_fields.setdefault('is_staff', False)
#         extra_fields.setdefault('is_superuser', False)
#         return self._create_user(registration_number, password, **extra_fields)

#     def create_superuser(self, registration_number, password, **extra_fields):
#         """Create and save a SuperUser with the given registration number."""
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)

#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

        # return self._create_user(registration_number, password, **extra_fields)

        
def create_from_college_data(self, college_data_id):
    """Create a User from CollegeData, generating a secure voter_id and password.
    Uses email from CollegeData if available and valid, otherwise defers email setting.
    Modified to use UUID for voter_id.
    """
    from .models import CollegeData
    college_data = CollegeData.objects.get(id=college_data_id)
    if college_data.is_used:
        raise ValueError('College data already used')

    # Generate random password and voter_id
    default_password = secrets.token_hex(8)
    voter_id = str(uuid.uuid4())  # Use UUID for secure, unique voter_id

    # Prepare user creation arguments
    user_creation_kwargs = {
        'registration_number': college_data.registration_number,
        'password': default_password,
        'first_name': college_data.first_name,
        'last_name': college_data.last_name,
        'course': college_data.course,
        'voter_id': voter_id,
        'is_verified': False
    }

    # Only pass email if it's present and not just whitespace in CollegeData
    # This prevents passing '' which causes the unique constraint error
    if college_data.email and college_data.email.strip():
        user_creation_kwargs['email'] = college_data.email

    # Create user with prepared arguments
    user = self.create_user(**user_creation_kwargs)

    college_data.mark_as_used()
    return user, default_password

# V[01]
    # def create_from_college_data(self, college_data_id):
    #     """Create a User from CollegeData, generating a secure voter_id and password.
    #     # Modified to use UUID for voter_id for stronger anonymity and consistency with VoterToken.
    #     """
    #     from .models import CollegeData
    #     college_data = CollegeData.objects.get(id=college_data_id)
    #     if college_data.is_used:
    #         raise ValueError('College data already used')
        
    #     # Generate random password and voter_id
    #     default_password = secrets.token_hex(8)
    #     voter_id = str(uuid.uuid4())  # Use UUID for secure, unique voter_id
        
    #     user = self.create_user(
    #         registration_number=college_data.registration_number,
    #         password=default_password,
    #         first_name=college_data.first_name,
    #         last_name=college_data.last_name,
    #         course=college_data.course,
    #         email=college_data.email,
    #         voter_id=voter_id,
    #         is_verified=False
    #     )
        
    #     college_data.mark_as_used()
    #     return user, default_password

    def generate_voter_token(self, user_id, election_id):
        """Generate a VoterToken for a user and election.
        # Added to support async VoterToken creation for anonymous voting.
        """
        from election.models import VoterToken, Election
        user = self.get(id=user_id)
        if not user.can_vote():
            raise ValueError('User is not eligible to vote')
        
        election = Election.objects.get(id=election_id)
        if not election.is_ongoing():
            raise ValueError('Election is not ongoing')
        
        token, created = VoterToken.objects.get_or_create(
            user=user,
            election=election,
            defaults={'token': uuid.uuid4()}
        )
        if not created and token.is_used:
            raise ValueError('Voter token already used')
        
        return token

class State(models.Model):
    """Model representing a state/region."""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'states'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

class Course(models.Model):
    """Model representing a course offered by the university."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        db_table = 'courses'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
        ]

class User(AbstractUser):
    """Custom User model with registration number authentication."""
    
    ROLE_VOTER = 'voter'
    ROLE_CANDIDATE = 'candidate'
    ROLE_CLASS_LEADER = 'class_leader'
    ROLE_COMMISSIONER = 'commissioner'
    
    ROLE_CHOICES = [
        (ROLE_VOTER, 'Voter'),
        (ROLE_CANDIDATE, 'Candidate'),
        (ROLE_CLASS_LEADER, 'Class Leader'),
        (ROLE_COMMISSIONER, 'Commissioner'),
    ]
    
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_OTHER = 'other'
    
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
        (GENDER_OTHER, 'Other'),
    ]
    
    username = None
    
    # Fields
    registration_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[A-Z0-9/]+$',
            message='Registration number must contain only uppercase letters, numbers, or slashes.'
        )],
        help_text="University registration number (e.g., T/XXX/202X/XXX)"
    )
    email = models.EmailField(
        ('email address'),
        unique=True,
        null=True,
        blank=True,
        help_text="Required email for notifications and password resets",
    )
    voter_id = models.CharField(
        max_length=36,  # Increased to fit UUID format
        unique=True,
        null=True,
        blank=True,
        help_text="Unique voter ID for anonymous voting, auto-generated UUID"
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        help_text="User's gender for position eligibility"
    )
    state = models.ForeignKey(
        State,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User's state/region"
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User's academic course"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_VOTER,
        help_text="User's role in the election system"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether the user account is verified"
    )
    
    # Timestamps
    date_verified = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Authentication settings
    USERNAME_FIELD = 'registration_number'
    REQUIRED_FIELDS = ['email']
    
    objects = UserManager()
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.registration_number})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() if full_name.strip() else self.registration_number
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name or self.registration_number
    
    def is_voter(self):
        return self.role == self.ROLE_VOTER
    
    def is_candidate(self):
        return self.role == self.ROLE_CANDIDATE
    
    def is_class_leader(self):
        return self.role == self.ROLE_CLASS_LEADER
    
    def is_commissioner(self):
        return self.role == self.ROLE_COMMISSIONER
    
    def can_vote(self):
        """Check if user can participate in voting."""
        return self.is_verified and self.voter_id and (self.is_voter() or self.is_candidate())
    
    def can_manage_elections(self):
        """Check if user can manage elections."""
        return self.is_commissioner() or self.is_staff
    
    def can_upload_college_data(self):
        """Check if user can upload college data."""
        return self.is_class_leader() or self.is_commissioner() or self.is_staff
    
    def has_voted_in_election(self, election_id):
        """Check if user has voted in a specific election.
        # Added to support vote validation in Celery tasks.
        """
        from election.models import VoterToken
        return VoterToken.objects.filter(
            user=self,
            election_id=election_id,
            is_used=True
        ).exists()
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['role', 'is_verified']),
            models.Index(fields=['state', 'course']),
            models.Index(fields=['email']),
            models.Index(fields=['gender']),
            models.Index(fields=['voter_id']),
        ]

class CollegeData(models.Model):
    """Model for storing pre-uploaded college data by Class Leaders."""
    registration_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[A-Z0-9/]+$',
            message='Registration number must contain only uppercase letters, numbers, or slashes.'
        )]
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(
        help_text="Required email for user account creation",
        blank=True
    )
    voter_id = models.CharField(
        max_length=36,  # Increased to fit UUID format
        unique=True,
        null=True,
        blank=True,
        help_text="Unique voter ID for anonymous voting, auto-generated UUID"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': [User.ROLE_CLASS_LEADER, User.ROLE_COMMISSIONER]},
        help_text="Class leader or commissioner who uploaded this data"
    )
    is_used = models.BooleanField(
        default=False,
        help_text="Whether this data has been used to create a user account"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processed', 'Processed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text="Processing status for async tasks"
    )
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.registration_number})"
    
    def mark_as_used(self):
        """Mark this college data as used for user creation.
        # Modified to set voter_id if not provided.
        """
        if not self.voter_id:
            self.voter_id = str(uuid.uuid4())
        self.is_used = True
        self.status = 'processed'
        self.save(update_fields=['is_used', 'status', 'voter_id'])
    
    class Meta:
        db_table = 'college_data'
        verbose_name = 'College Data'
        verbose_name_plural = 'College Data'
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['course', 'is_used']),
            models.Index(fields=['status']),
            models.Index(fields=['voter_id']),
        ]
