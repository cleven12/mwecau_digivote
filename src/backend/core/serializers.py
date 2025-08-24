from rest_framework import serializers
from election.models import User, State, Course
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['registration_number', 'first_name', 'last_name', 'email', 'is_verified', 'role']
class ForgotPasswordSerializer(serializers.Serializer):
    registration_number = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)