from rest_framework import serializers
from .models import Election, ElectionLevel, Position, Candidate, VoterToken, Vote
from core.models import User, Course, State
from django.utils import timezone


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
    course_details = CourseSerializer(source='course', read_only=True)
    state_details = StateSerializer(source='state', read_only=True)

    class Meta:
        model = ElectionLevel
        fields = ['id', 'name', 'code', 'type', 'description', 'course', 'state', 'course_details', 'state_details']


class ElectionListSerializer(serializers.ModelSerializer):
    """Serializer for listing elections."""
    levels = ElectionLevelListSerializer(many=True, read_only=True)

    class Meta:
        model = Election
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'is_active', 'has_ended', 'levels']


class PositionDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed Position view."""
    class Meta:
        model = Position
        fields = ['id', 'title', 'description', 'gender_restriction']


class CandidateListSerializer(serializers.ModelSerializer):
    """Serializer for listing candidates, including image URL and basic user info."""
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_registration_number = serializers.CharField(source='user.registration_number', read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = ['id', 'user_full_name', 'user_registration_number', 'bio', 'platform', 'image_url']

    def get_image_url(self, obj):
        """Generate the full URL for the candidate's image."""
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class VoterTokenSerializer(serializers.ModelSerializer):
    """Serializer for VoterToken, showing key details."""
    election_level_details = ElectionLevelListSerializer(source='election_level', read_only=True)
    
    class Meta:
        model = VoterToken
        fields = ['id', 'token', 'election_level', 'election_level_details', 'is_used', 'expiry_date', 'created_at']
        read_only_fields = ['token', 'is_used', 'created_at']


class VoteCreateSerializer(serializers.Serializer):
    """Serializer for casting a vote. Takes UUID token string and candidate ID."""
    token = serializers.UUIDField(help_text="The UUID string of the VoterToken")
    candidate_id = serializers.IntegerField(help_text="The ID of the Candidate to vote for")

    def validate_token(self, value):
        """Check if the token UUID exists."""
        try:
            token_obj = VoterToken.objects.get(token=value)
            self.token_obj = token_obj
            return value
        except VoterToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token UUID provided.")

    def validate(self, data):
        """Perform complex validation involving multiple fields and the token object."""
        token_obj = getattr(self, 'token_obj', None)
        candidate_id = data.get('candidate_id')
        
        if not token_obj or not candidate_id:
            raise serializers.ValidationError("Token and candidate ID are required.")

        if not token_obj.is_valid():
            raise serializers.ValidationError("Token is either used or expired.")

        election = token_obj.election
        if not election.is_ongoing():
            raise serializers.ValidationError("The associated election is not currently active.")

        try:
            candidate = Candidate.objects.select_related(
                'position__election_level'
            ).get(id=candidate_id)
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("Candidate not found.")

        if candidate.election != election:
            raise serializers.ValidationError("Candidate does not belong to the election associated with the token.")

        if candidate.position.election_level != token_obj.election_level:
            raise serializers.ValidationError("Candidate's position level does not match the level authorized by the token.")

        self.election = election
        self.election_level = token_obj.election_level
        self.candidate = candidate

        return data


class ResultSerializer(serializers.Serializer):
    """Serializer for individual candidate results within a position."""
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField() 
    candidate_image_url = serializers.SerializerMethodField() 
    vote_count = serializers.IntegerField()
    vote_percentage = serializers.FloatField()

    def get_candidate_image_url(self, obj):
        """Placeholder for image URL generation."""
        return None


class PositionResultSerializer(serializers.Serializer):
    """Serializer aggregating results for a single position."""
    position_id = serializers.IntegerField()
    position_title = serializers.CharField()
    total_votes_cast = serializers.IntegerField() 
    candidates = ResultSerializer(many=True)
