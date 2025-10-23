# core/serializers.py
import logging
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework.exceptions import ValidationError
from django.contrib.auth import authenticate

from core.models import User, State, Course 
logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    course = serializers.CharField(source='course.name', read_only=True, allow_null=True)

    email = serializers.EmailField(allow_null=True, allow_blank=True, required=False)
    is_verified = serializers.BooleanField(default=False)
    role = serializers.CharField(default='voter')

    class Meta:
        model = User
        fields = ['registration_number', 'first_name', 'last_name', 'email', 'is_verified', 'role', 'course']

    def to_internal_value(self, data):
        """Handle course ID input and validate."""
        data = data.copy()
        course_id = data.get('course')
        if course_id:
            try:
                course = Course.objects.get(pk=course_id)
                data['course'] = course.pk
                logger.debug(f"to_internal_value: course_id={course_id}, course_name={course.name}")
            except Course.DoesNotExist:
                logger.error(f"Course with pk={course_id} does not exist")
                raise serializers.ValidationError({'course': 'Invalid course ID'})
        return super().to_internal_value(data)

class ForgotPasswordSerializer(serializers.Serializer):
    registration_number = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        registration_number = attrs.get('registration_number')
        password = attrs.get('password')
        
        # Use the imported authenticate function
        user = authenticate(
            request=self.context.get('request'),
            registration_number=registration_number,
            password=password
        )

        if user is None:
            raise ValidationError('Invalid registration number or password')
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }



# V[0] 
# import logging
# from rest_framework import serializers
# from core.models import User, State, Course
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from django.contrib.auth import authenticate

# logger = logging.getLogger(__name__)

# class UserSerializer(serializers.ModelSerializer):
#     course = serializers.CharField(source='course.name', read_only=True, allow_null=True)

#     email = serializers.EmailField(allow_null=True, allow_blank=True, required=False)
#     is_verified = serializers.BooleanField(default=False)
#     role = serializers.CharField(default='voter')

#     class Meta:
#         model = User
#         fields = ['registration_number', 'first_name', 'last_name', 'email', 'is_verified', 'role', 'course']

#     def to_internal_value(self, data):
#         """Handle course ID input and validate."""
#         data = data.copy()  # Make mutable copy of data
#         course_id = data.get('course')
#         if course_id:
#             try:
#                 course = Course.objects.get(pk=course_id)
#                 data['course'] = course.pk  # Ensure course ID is passed to model
#                 logger.debug(f"to_internal_value: course_id={course_id}, course_name={course.name}")
#             except Course.DoesNotExist:
#                 logger.error(f"Course with pk={course_id} does not exist")
#                 raise serializers.ValidationError({'course': 'Invalid course ID'})
#         return super().to_internal_value(data)

# class ForgotPasswordSerializer(serializers.Serializer):
#     registration_number = serializers.CharField(max_length=20)
#     email = serializers.EmailField()
#     state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())
#     course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
#     first_name = serializers.CharField(max_length=50, required=False)
#     last_name = serializers.CharField(max_length=50, required=False)

# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     def validate(self, attrs):
#         registration_number = attrs.get('registration_number')
#         password = attrs.get('password')
#         user = authenticate(
#             request=self.context.get('request'),
#             registration_number=registration_number,
#             password=password
#         )
#         if user is None:
#             raise serializers.ValidationError('Invalid registration number or password')
#         refresh = RefreshToken.for_user(user) # type: ignore
#         return {
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#         }