
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Define a model manager for User model with registration number authentication."""

    use_in_migrations = True

    def _create_user(self, registration_number, password, **extra_fields):
        """Create and save a User with the given registration number and password."""
        if not registration_number:
            raise ValueError('The given registration number must be set')
        
        # Normalize email if provided
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

class State(models.Model):
    """Model representing a state/region."""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'state_majimbo'
        ordering = ['name']

class Course(models.Model):
    """Model representing a course offered by the university."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    class Meta:
        db_table = 'course'
        ordering = ['code']

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
    
    # Remove username field and use registration_number for authentication
    username = None
    
    # Fields
    registration_number = models.CharField(
        max_length=20, 
        unique=True,
        help_text="University registration number used for login"
    )
    email = models.EmailField(
        _('email address'), 
        null=True, 
        blank=True,
        help_text="Optional email for notifications only"
    )
    voter_id = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        help_text="Optional voter identification number"
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
    REQUIRED_FIELDS = []  # Email is optional
    
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
    
    # Role checking methods
    def is_voter(self):
        return self.role == self.ROLE_VOTER
    
    def is_candidate(self):
        return self.role == self.ROLE_CANDIDATE
    
    def is_class_leader(self):
        return self.role == self.ROLE_CLASS_LEADER
    
    def is_commissioner(self):
        return self.role == self.ROLE_COMMISSIONER
    
    # Permission helpers
    def can_vote(self):
        """Check if user can participate in voting."""
        return self.is_verified and (self.is_voter() or self.is_candidate())
    
    def can_manage_elections(self):
        """Check if user can manage elections."""
        return self.is_commissioner() or self.is_staff
    
    def can_upload_college_data(self):
        """Check if user can upload college data."""
        return self.is_class_leader() or self.is_commissioner() or self.is_staff
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['role', 'is_verified']),
            models.Index(fields=['state', 'course']),
            models.Index(fields=['email']),
        ]

class CollegeData(models.Model):
    """Model for storing pre-uploaded college data by Class Leaders."""
    registration_number = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
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
    
    def __str__(self):
        return f"{self.full_name} ({self.registration_number})"
    
    def mark_as_used(self):
        """Mark this college data as used for user creation."""
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    class Meta:
        db_table = 'college_data'
        verbose_name = 'College Data'
        verbose_name_plural = 'College Data'
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['course', 'is_used']),
        ]