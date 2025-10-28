from rest_framework import serializers
from .models import Candidate, Position
from django.core.validators import FileExtensionValidator
from django.conf import settings

class CandidateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new candidate application."""
    class Meta:
        model = Candidate
        fields = ['position', 'bio', 'platform', 'image']
        extra_kwargs = {
            'bio': {'required': True},
            'platform': {'required': True},
            'image': {
                'required': False,
                'allow_null': True,
                'validators': [
                    FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png']),
                ]
            }
        }

    def validate_position(self, value):
        """
        Validate that:
        1. Position is open for applications
        2. User meets gender requirements if any
        3. User hasn't already applied for this position
        4. User meets course/state requirements for the position's level
        """
        user = self.context['request'].user

        # Check if already applied
        if Candidate.objects.filter(
            user=user,
            position__election=value.election_level.elections.first()
        ).exists():
            raise serializers.ValidationError(
                "You have already applied for a position in this election."
            )

        # Check gender restrictions
        if value.gender_restriction != Position.GENDER_ANY:
            if not user.gender or user.gender != value.gender_restriction:
                raise serializers.ValidationError(
                    f"This position is restricted to {value.get_gender_restriction_display()} candidates."
                )

        # Check level-specific eligibility
        level = value.election_level
        if level.type == 'course':
            if not user.course or user.course != level.course:
                raise serializers.ValidationError(
                    "You can only apply for positions in your course."
                )
        elif level.type == 'state':
            if not user.state or user.state != level.state:
                raise serializers.ValidationError(
                    "You can only apply for positions in your state."
                )

        return value

    def create(self, validated_data):
        """Create candidate with current user."""
        user = self.context['request'].user
        election = validated_data['position'].election_level.elections.first()
        
        return Candidate.objects.create(
            user=user,
            election=election,
            **validated_data
        )


class CandidateDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for candidate profile, including application status."""
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_registration_number = serializers.CharField(source='user.registration_number', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    election_title = serializers.CharField(source='election.title', read_only=True)
    election_level_name = serializers.CharField(source='position.election_level.name', read_only=True)
    image_url = serializers.SerializerMethodField()
    vote_count = serializers.IntegerField(read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            'id', 'user_full_name', 'user_registration_number',
            'position_title', 'election_title', 'election_level_name',
            'bio', 'platform', 'image_url', 'vote_count', 'can_edit',
            'created_at'
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None

    def get_can_edit(self, obj):
        """Check if requesting user can edit this candidate profile."""
        user = self.context['request'].user
        # Can edit if admin/commissioner or if it's your own profile
        return user.is_staff or user.is_commissioner() or obj.user == user