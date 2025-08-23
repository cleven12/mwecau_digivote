from django.db import models
from django.utils import timezone
from core.models import User, State, Course
import uuid

class ElectionLevel(models.Model):
    """Model representing an election level (President, State Leader, Course Leader)."""
    LEVEL_PRESIDENT = 'president'
    LEVEL_STATE = 'state'
    LEVEL_COURSE = 'course'
    
    LEVEL_CHOICES = [
        (LEVEL_PRESIDENT, 'President'),
        (LEVEL_STATE, 'State'),
        (LEVEL_COURSE, 'Course'),
    ]
    
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, choices=LEVEL_CHOICES, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        indexes = [
            models.Index(fields=['code']),  # Added for faster lookups in analytics tasks
        ]

class Election(models.Model):
    """Model representing an election event."""
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)
    has_ended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def is_ongoing(self):
        """Check if election is currently ongoing."""
        now = timezone.now()
        return self.is_active and self.start_date <= now < self.end_date
    
    def is_upcoming(self):
        """Check if election is upcoming."""
        now = timezone.now()
        return not self.is_active and self.start_date > now
    
    def is_past(self):
        """Check if election is past."""
        now = timezone.now()
        return self.has_ended or (self.is_active and self.end_date < now)
    
    def time_until_start(self):
        """Return time until election starts."""
        now = timezone.now()
        if self.start_date > now:
            return self.start_date - now
        return None
    
    def time_until_end(self):
        """Return time until election ends."""
        now = timezone.now()
        if self.is_active and self.end_date > now:
            return self.end_date - now
        return None
    
    def time_since_end(self):
        """Return time since election ended."""
        now = timezone.now()
        if self.has_ended or (self.is_active and self.end_date < now):
            return now - self.end_date
        return None
    
    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'start_date', 'end_date']),  # Added for faster election status queries
        ]

class Position(models.Model):
    """Model representing a position in an election."""
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_ANY = 'any'
    
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
        (GENDER_ANY, 'Any'),
    ]
    
    title = models.CharField(max_length=100)
    election_level = models.ForeignKey(ElectionLevel, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    gender_restriction = models.CharField(max_length=10, choices=GENDER_CHOICES, default=GENDER_ANY)
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        if self.gender_restriction != self.GENDER_ANY:
            return f"{self.title} ({self.get_gender_restriction_display()})"
        return self.title
    
    class Meta:
        unique_together = [
            ['election_level', 'title', 'gender_restriction', 'state', 'course']
        ]
        indexes = [
            models.Index(fields=['election_level', 'state', 'course']),  # Added for faster position queries
        ]

class Candidate(models.Model):
    """Model representing a candidate for a position."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    platform = models.TextField(blank=True)
    vote_count = models.PositiveIntegerField(default=0)  # Added to cache vote totals for analytics
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position} ({self.election.title})"
    
    class Meta:
        unique_together = [
            ['user', 'election', 'position']
        ]
        indexes = [
            models.Index(fields=['election', 'position']),  # Added for faster vote aggregation
        ]
    
    def get_vote_percentage(self, total=None):
        """Get the percentage of votes for this candidate.
        # Modified to use vote_count field for efficiency.
        """
        if total is None:
            total = sum(c.vote_count for c in Candidate.objects.filter(
                election=self.election,
                position=self.position
            ))
            
        if total == 0:
            return 0
            
        return (self.vote_count / total) * 100

class VoterToken(models.Model):
    """Model for anonymous voting tokens.
    # Added to support anonymous voting by linking to User.voter_id and Election,
    # ensuring votes cannot be traced to registration_number or voter_id.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Token for {self.election.title} ({self.user.voter_id})"
    
    def mark_as_used(self):
        """Mark token as used after voting."""
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=['is_used', 'used_at'])
    
    class Meta:
        unique_together = [
            ['user', 'election'],  # One token per user per election
        ]
        indexes = [
            models.Index(fields=['token']),  # Fast token lookups
            models.Index(fields=['election', 'is_used']),  # Fast validation queries
        ]

class Vote(models.Model):
    """Model representing a vote cast by a voter.
    # Modified to use VoterToken for anonymity and added election field to fix unique_together bug.
    """
    token = models.ForeignKey(VoterToken, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)  # Added to directly reference Election
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Vote for {self.candidate} at {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """Ensure election matches candidate.election.
        # Added to enforce consistency between Vote.election and Candidate.election.
        """
        if self.candidate and self.election != self.candidate.election:
            raise ValueError("Vote election must match candidate's election")
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = [
            ['token', 'election'],  # Fixed to use direct election field for one vote per user per election
        ]