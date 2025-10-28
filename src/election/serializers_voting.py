from rest_framework import serializers
from .models import Position, Candidate, Election, ElectionLevel, Vote
from core.models import User

class PositionCandidateSerializer(serializers.ModelSerializer):
    """Serializer for listing candidates in a voting context."""
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    registration_number = serializers.CharField(source='user.registration_number', read_only=True)
    image_url = serializers.SerializerMethodField()
    vote_count = serializers.IntegerField(read_only=True)
    has_voted = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = [
            'id', 'user_full_name', 'registration_number',
            'bio', 'platform', 'image_url', 'vote_count',
            'has_voted'
        ]
        
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
        
    def get_has_voted(self, obj):
        """Check if the requesting user has voted for this position."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
            
        # Get from context if available (bulk loaded)
        user_votes = self.context.get('user_votes', {})
        if user_votes:
            return obj.position_id in user_votes
            
        # Otherwise query directly
        return Vote.objects.filter(
            voter=request.user,
            election=obj.election,
            election_level=obj.position.election_level
        ).exists()


class ElectionPositionSerializer(serializers.ModelSerializer):
    """Serializer for positions in an election with their candidates."""
    candidates = serializers.SerializerMethodField()
    level_name = serializers.CharField(source='election_level.name')
    level_type = serializers.CharField(source='election_level.type')
    total_votes = serializers.IntegerField(read_only=True)
    user_can_vote = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = [
            'id', 'title', 'description', 'level_name', 'level_type',
            'gender_restriction', 'candidates', 'total_votes',
            'user_can_vote'
        ]
        
    def get_candidates(self, obj):
        # Get candidates for this position
        candidates = (
            obj.candidates
            .select_related('user')
            .order_by('-vote_count', 'user__first_name')
        )
        
        return PositionCandidateSerializer(
            candidates,
            many=True,
            context=self.context
        ).data
        
    def get_user_can_vote(self, obj):
        """Check if user has a valid token for this position's level."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
            
        # Get from context if available (bulk loaded)
        user_tokens = self.context.get('user_tokens', {})
        if user_tokens:
            # Check if user has unused token for this level
            return obj.election_level_id in user_tokens
            
        # Otherwise query directly
        from .models import VoterToken
        return VoterToken.objects.filter(
            user=request.user,
            election_level=obj.election_level,
            is_used=False
        ).exists()


class ElectionVotingSerializer(serializers.ModelSerializer):
    """Serializer for election details in voting context."""
    positions = serializers.SerializerMethodField()
    
    class Meta:
        model = Election
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'is_active', 'positions'
        ]
        
    def get_positions(self, obj):
        # Get positions for this election's levels
        positions = Position.objects.filter(
            election_level__in=obj.levels.all()
        ).select_related(
            'election_level'
        ).annotate(
            total_votes=models.Count('candidates__votes')
        ).order_by(
            'election_level__type',
            'title'
        )
        
        # Bulk load user's voting status
        request = self.context.get('request')
        context = self.context.copy()
        
        if request and request.user.is_authenticated:
            # Get user's used tokens
            from .models import VoterToken
            used_tokens = VoterToken.objects.filter(
                user=request.user,
                election=obj,
                is_used=True
            ).values_list('election_level_id', flat=True)
            context['user_votes'] = set(used_tokens)
            
            # Get user's available tokens
            available_tokens = VoterToken.objects.filter(
                user=request.user,
                election=obj,
                is_used=False
            ).values_list('election_level_id', flat=True)
            context['user_tokens'] = set(available_tokens)
        
        return ElectionPositionSerializer(
            positions,
            many=True,
            context=context
        ).data