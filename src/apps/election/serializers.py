# election/serializers.py
from rest_framework import serializers
from .models import Election, ElectionLevel, Position, Candidate, VoterToken, Vote
from apps.core .models import User, Course, State # Import related models for nested serialization if needed
from django.urls import reverse
from django.utils import timezone

# --- Serializers for related models used in nested representations ---
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'code']

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name']

class ElectionLevelListSerializer(serializers.ModelSerializer):
    """Serializer for listing ElectionLevels, including type-specific details."""
    # Include related Course/State details when relevant
    course_details = CourseSerializer(source='course', read_only=True)
    state_details = StateSerializer(source='state', read_only=True)

    class Meta:
        model = ElectionLevel
        fields = ['id', 'name', 'code', 'type', 'description', 'course', 'state', 'course_details', 'state_details']

class ElectionListSerializer(serializers.ModelSerializer):
    """Serializer for listing elections."""
    # Use the simpler serializer for the list view
    levels = ElectionLevelListSerializer(many=True, read_only=True)

    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'is_active', 'has_ended', 'levels']

# --- Detailed Serializers ---
class PositionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed Position view, potentially including candidates."""
    class Meta:
        model = Position
        fields = ['id', 'title', 'description', 'gender_restriction'] # Add more if needed

class CandidateListSerializer(serializers.ModelSerializer):
    """Serializer for listing candidates, including image URL and basic user info."""
    # Get user details directly
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_registration_number = serializers.CharField(source='user.registration_number', read_only=True)
    
    # Handle image URL safely
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = ['id', 'user_full_name', 'user_registration_number', 'bio', 'platform', 'image_url']
        # Note: vote_count is not a field, use get_vote_count method if needed in views

    def get_image_url(self, obj):
        """Generate the full URL for the candidate's image."""
        request = self.context.get('request')
        if obj.image and request:
            # Use request.build_absolute_uri for correct domain/path
            return request.build_absolute_uri(obj.image.url)
        return None # Return None if no image or request context

class VoterTokenSerializer(serializers.ModelSerializer):
    """Serializer for VoterToken, showing key details."""
    # Optionally serialize related level details
    # election_level_details = ElectionLevelListSerializer(source='election_level', read_only=True)
    
    class Meta:
        model = VoterToken
        fields = ['id', 'token', 'election_level', 'is_used', 'expiry_date', 'created_at']
        # fields = ['id', 'token', 'election_level', 'election_level_details', 'is_used', 'expiry_date', 'created_at']
        read_only_fields = ['token', 'is_used', 'created_at'] # Token and status are set by system

# --- Serializers for Creation/Specific Actions ---
class VoteCreateSerializer(serializers.Serializer):
    """Serializer for casting a vote. Takes UUID token string and candidate ID."""
    token = serializers.UUIDField(help_text="The UUID string of the VoterToken")
    candidate_id = serializers.IntegerField(help_text="The ID of the Candidate to vote for")

    def validate_token(self, value):
        """Check if the token UUID exists."""
        try:
            token_obj = VoterToken.objects.get(token=value)
            self.token_obj = token_obj # Store for later use in view
            return value
        except VoterToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token UUID provided.")

    def validate(self, data):
        """Perform complex validation involving multiple fields and the token object."""
        token_obj = getattr(self, 'token_obj', None)
        candidate_id = data.get('candidate_id')
        
        if not token_obj or not candidate_id:
            # Should not happen if individual field validation passed, but good practice
            raise serializers.ValidationError("Token and candidate ID are required.")

        # --- Check Token Validity ---
        if not token_obj.is_valid():
             raise serializers.ValidationError("Token is either used or expired.")

        # --- Check Election is Ongoing ---
        election = token_obj.election
        if not election.is_ongoing():
             raise serializers.ValidationError("The associated election is not currently active.")

        # --- Check Candidate Exists and Matches Election/Level ---
        try:
            candidate = Candidate.objects.select_related(
                'position__election_level' # Optimize query
            ).get(id=candidate_id)
        except Candidate.DoesNotExist:
             raise serializers.ValidationError("Candidate not found.")

        if candidate.election != election:
             raise serializers.ValidationError("Candidate does not belong to the election associated with the token.")

        if candidate.position.election_level != token_obj.election_level:
             raise serializers.ValidationError("Candidate's position level does not match the level authorized by the token.")

        # --- Store validated objects for use in the view ---
        self.election = election
        self.election_level = token_obj.election_level
        self.candidate = candidate

        return data

# Serializer for Results (example structure)
class ResultSerializer(serializers.Serializer):
    """Serializer for individual candidate results within a position."""
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField() # Or use nested serializer
    candidate_image_url = serializers.SerializerMethodField() # Or use nested serializer
    vote_count = serializers.IntegerField()
    vote_percentage = serializers.FloatField()

    # If Candidate object is passed, you can get image URL like this:
    # def get_candidate_image_url(self, obj):
    #     request = self.context.get('request')
    #     if obj.image and request:
    #         return request.build_absolute_uri(obj.image.url)
    #     return None

# Serializer for Position Results
class PositionResultSerializer(serializers.Serializer):
    """Serializer aggregating results for a single position."""
    position_id = serializers.IntegerField()
    position_title = serializers.CharField()
    total_votes_cast = serializers.IntegerField() # For this position/level
    candidates = ResultSerializer(many=True)
