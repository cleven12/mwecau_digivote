from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import User, State, Course
import uuid


class ElectionLevel(models.Model):
    """Model representing a specific type and scope of election."""
    TYPE_PRESIDENT = 'president'
    TYPE_COURSE = 'course'
    TYPE_STATE = 'state'
    TYPE_CHOICES = [
        (TYPE_PRESIDENT, 'President'),
        (TYPE_COURSE, 'Course Leader'),
        (TYPE_STATE, 'State Leader'),
    ]

    name = models.CharField(max_length=100, help_text="Descriptive name for the level")
    code = models.CharField(max_length=50, unique=True, help_text="Unique code for the level")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, help_text="General category of the election level")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, help_text="Specific course this level applies to")
    state = models.ForeignKey(State, on_delete=models.CASCADE, null=True, blank=True, help_text="Specific state this level applies to")
    description = models.TextField(blank=True, help_text="Optional description of the level")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'election_levels'
        verbose_name = 'Election Level'
        verbose_name_plural = 'Election Levels'
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['code']),
            models.Index(fields=['course']),
            models.Index(fields=['state']),
        ]

    def __str__(self):
        if self.type == self.TYPE_COURSE and self.course:
            return f"{self.name} ({self.course.name})"
        elif self.type == self.TYPE_STATE and self.state:
            return f"{self.name} ({self.state.name})"
        return self.name

    def clean(self):
        """Ensure data integrity based on the level type."""
        if self.type == self.TYPE_COURSE:
            if not self.course:
                raise ValidationError("Course level must have a specific course assigned.")
            if self.state:
                raise ValidationError("Course level should not have a state assigned.")
        elif self.type == self.TYPE_STATE:
            if not self.state:
                raise ValidationError("State level must have a specific state assigned.")
            if self.course:
                raise ValidationError("State level should not have a course assigned.")
        elif self.type == self.TYPE_PRESIDENT:
            if self.course or self.state:
                raise ValidationError("President level should not have a course or state assigned.")

    def save(self, *args, **kwargs):
        """Override save to enforce validation on save."""
        self.clean()
        super().save(*args, **kwargs)


class Election(models.Model):
    """Model representing an election event, potentially spanning multiple levels."""
    title = models.CharField(max_length=200, help_text="Title of the election")
    description = models.TextField(blank=True, help_text="Description of the election")
    start_date = models.DateTimeField(help_text="Date and time the election starts")
    end_date = models.DateTimeField(help_text="Date and time the election ends")
    is_active = models.BooleanField(default=False, help_text="Whether the election is currently active for voting")
    has_ended = models.BooleanField(default=False, help_text="Whether the election has officially ended and results are final")
    levels = models.ManyToManyField(ElectionLevel, related_name='elections', help_text="Election levels included in this election")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'elections'
        verbose_name = 'Election'
        verbose_name_plural = 'Elections'
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['has_ended']),
        ]

    def __str__(self):
        return self.title

    def is_ongoing(self):
        """Check if the election is currently within its active voting period."""
        now = timezone.now()
        return self.is_active and self.start_date <= now < self.end_date

    def activate(self, notify_voters=True):
        """
        Activate the election and optionally notify voters.
        Returns True if activation was successful, False if already active.
        """
        if self.has_ended:
            raise ValidationError("Cannot activate an election that has ended")
        
        if self.is_active:
            return False
            
        # Validate election has required data
        if not self.start_date or not self.end_date:
            raise ValidationError("Election must have start and end dates")
            
        if not self.levels.exists():
            raise ValidationError("Election must have at least one level")
            
        now = timezone.now()
        if self.end_date <= now:
            raise ValidationError("Cannot activate an election that has already ended")
            
        self.is_active = True
        self.save(update_fields=['is_active'])
        
        if notify_voters:
            from .tasks import notify_voters_of_active_election
            notify_voters_of_active_election(self.id)
            
        return True
        
    def deactivate(self):
        """
        Deactivate the election.
        Returns True if deactivation was successful, False if already inactive.
        """
        if not self.is_active:
            return False
            
        self.is_active = False
        self.save(update_fields=['is_active'])
        return True
    def activate(self):
        """Activate the election and generate voter tokens."""
        from .tasks import notify_voters_of_active_election
        if not self.is_active:
            self.is_active = True
            self.save()
            # Generate tokens and send notifications
            notify_voters_of_active_election(self.id)

    def save(self, *args, **kwargs):
        """Override save, potentially to trigger notifications."""
        super().save(*args, **kwargs)


class Position(models.Model):
    """Model representing a specific position to be filled within an election level."""
    GENDER_MALE = 'male'
    GENDER_FEMALE = 'female'
    GENDER_ANY = 'any'
    GENDER_CHOICES = [
        (GENDER_MALE, 'Male'),
        (GENDER_FEMALE, 'Female'),
        (GENDER_ANY, 'Any'),
    ]

    title = models.CharField(max_length=100, help_text="Title of the position")
    election_level = models.ForeignKey(ElectionLevel, on_delete=models.CASCADE, related_name='positions', help_text="The election level this position belongs to")
    description = models.TextField(blank=True, help_text="Description of the position's responsibilities")
    gender_restriction = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default=GENDER_ANY,
        help_text="Gender restriction for candidates (if any)"
    )

    class Meta:
        db_table = 'positions'
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'
        unique_together = ['election_level', 'title', 'gender_restriction']
        indexes = [
            models.Index(fields=['election_level']),
        ]

    def __str__(self):
        base_str = f"{self.title}"
        if self.gender_restriction != self.GENDER_ANY:
            base_str += f" ({self.get_gender_restriction_display()})"
        return base_str


class Candidate(models.Model):
    """Model representing a user running for a specific position in an election."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='candidacies', help_text="The user who is the candidate")
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates', help_text="The election they are running in")
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates', help_text="The specific position they are running for")
    bio = models.TextField(blank=True, help_text="Biography or statement from the candidate")
    platform = models.TextField(blank=True, help_text="Campaign platform or key points")
    image = models.ImageField(upload_to='candidate_images/', null=True, blank=True, help_text="Profile image of the candidate")
    vote_count = models.PositiveIntegerField(default=0, help_text="Cached count of votes received")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidates'
        verbose_name = 'Candidate'
        verbose_name_plural = 'Candidates'
        unique_together = ['user', 'election']  # One candidacy per election
        indexes = [
            models.Index(fields=['election', 'position']),
            models.Index(fields=['user']),
            models.Index(fields=['vote_count']),  # For sorting by votes
        ]
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position.title} ({self.election.title})"
        
    def update_vote_count(self):
        """Update the cached vote count."""
        self.vote_count = self.votes.count()
        self.save(update_fields=['vote_count', 'updated_at'])
        
    def can_edit(self, user):
        """Check if given user can edit this candidate profile."""
        return (
            user.is_staff or
            user.is_commissioner() or
            self.user == user
        )
        
    def is_eligible(self):
        """
        Check if the candidate meets all eligibility requirements.
        Called during clean() to validate before saving.
        """
        if not self.user or not self.position:
            return False
            
        # Gender restriction check
        if (self.position.gender_restriction != Position.GENDER_ANY and
            self.user.gender != self.position.gender_restriction):
            return False
            
        # Level-specific checks
        level = self.position.election_level
        if level.type == level.TYPE_COURSE:
            if not self.user.course or self.user.course != level.course:
                return False
        elif level.type == level.TYPE_STATE:
            if not self.user.state or self.user.state != level.state:
                return False
            
        return True
        
    def clean(self):
        """Validate the candidate meets all requirements."""
        super().clean()
        
        if not self.is_eligible():
            raise ValidationError({
                'user': 'User does not meet the eligibility requirements for this position.'
            })
            
        # Ensure election matches position's election level
        if self.position and self.election:
            if self.position.election_level not in self.election.levels.all():
                raise ValidationError({
                    'position': 'Position must belong to an election level in this election.'
                })

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'candidates'
        verbose_name = 'Candidate'
        verbose_name_plural = 'Candidates'
        unique_together = ['user', 'election', 'position']
        indexes = [
            models.Index(fields=['election', 'position']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position} ({self.election.title})"

    def get_vote_count(self):
        """Calculate the current vote count for this candidate."""
        return self.votes.count()

    def get_vote_percentage(self, total_votes_for_position=None):
        """Calculate the vote percentage for this candidate."""
        if total_votes_for_position is None:
            total_votes_for_position = Vote.objects.filter(
                election=self.election,
                election_level=self.position.election_level
            ).count()
        if total_votes_for_position == 0:
            return 0.0
        return (self.get_vote_count() / total_votes_for_position) * 100


class VoterToken(models.Model):
    """Model for unique, per-level voting tokens issued to eligible users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voter_tokens', help_text="The user this token belongs to")
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='voter_tokens', help_text="The election this token is for")
    election_level = models.ForeignKey(ElectionLevel, on_delete=models.CASCADE, related_name='voter_tokens', help_text="The specific level within the election this token authorizes voting for")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, help_text="The unique token string")
    is_used = models.BooleanField(default=False, help_text="Whether this token has been used to cast a vote")
    expiry_date = models.DateTimeField(help_text="Date and time the token expires")
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True, help_text="Date and time the token was used")

    class Meta:
        db_table = 'voter_tokens'
        verbose_name = 'Voter Token'
        verbose_name_plural = 'Voter Tokens'
        unique_together = ['user', 'election', 'election_level']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['election', 'election_level']),
            models.Index(fields=['is_used']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        status = "Used" if self.is_used else "Unused"
        return f"Token for {self.user.get_full_name()} - {self.election.title} - {self.election_level} ({status})"

    def mark_as_used(self):
        """Mark the token as used."""
        if not self.is_used:
            self.is_used = True
            self.used_at = timezone.now()
            self.save(update_fields=['is_used', 'used_at'])

    def is_valid(self):
        """Check if the token is valid (not used and not expired)."""
        now = timezone.now()
        return not self.is_used and self.expiry_date > now


class Vote(models.Model):
    """Model representing a single vote cast by a user using a specific token for a candidate."""
    token = models.ForeignKey(VoterToken, on_delete=models.CASCADE, related_name='votes', help_text="The token used to cast this vote")
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='votes', help_text="The candidate voted for")
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='votes', help_text="The election")
    election_level = models.ForeignKey(ElectionLevel, on_delete=models.CASCADE, related_name='votes', help_text="The election level")
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes', help_text="The user who voted")

    timestamp = models.DateTimeField(auto_now_add=True, help_text="Date and time the vote was cast")

    class Meta:
        db_table = 'votes'
        verbose_name = 'Vote'
        verbose_name_plural = 'Votes'
        unique_together = ['token']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['candidate']),
            models.Index(fields=['election', 'election_level']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Vote by {self.token.user.get_full_name()} for {self.candidate} in {self.election.title} ({self.election_level})"

    def save(self, *args, **kwargs):
        """Override save to enforce data integrity rules."""
        # Auto-populate fields from token FIRST (before validation)
        if self.token:
            self.election = self.token.election
            self.election_level = self.token.election_level
            self.voter = self.token.user
        
        # Now validate the populated fields
        if self.candidate and self.election != self.candidate.election:
            raise ValidationError("Vote election must match candidate's election.")

        if self.candidate and self.election_level != self.candidate.position.election_level:
            raise ValidationError("Vote level must match candidate's position level.")

        if self.token and self.election != self.token.election:
            raise ValidationError("Vote election must match the token's election.")

        if self.token and self.election_level != self.token.election_level:
            raise ValidationError("Vote level must match the token's election level.")

        super().save(*args, **kwargs)
