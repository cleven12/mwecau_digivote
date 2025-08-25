import logging
import secrets
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.conf import settings

from core import serializers
from .models import User, CollegeData, State, Course
from .serializers import UserSerializer, ForgotPasswordSerializer
from election.models import Election, ElectionLevel, VoterToken
from .tasks import send_verification_email, send_password_reset_email, send_commissioner_contact_email

logger = logging.getLogger(__name__)

# API Views
class UserLoginView(APIView):
    """API endpoint for user login with registration_number and password."""
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate login credentials using serializer
        serializer = serializers.CustomTokenObtainPairSerializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class UserLogoutView(APIView):
    """API endpoint to logout by blacklisting refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserRegisterView(APIView):
    """API endpoint to validate registration number via CollegeData."""
    permission_classes = [AllowAny]

    def post(self, request):
        reg_number = request.data.get('registration_number', '').strip()
        try:
            college_data = CollegeData.objects.get(registration_number=reg_number)
            if User.objects.filter(registration_number=reg_number).exists():
                return Response({'error': 'Registration number already registered'}, status=status.HTTP_400_BAD_REQUEST)
            if college_data.is_used:
                return Response({'error': 'College data already used'}, status=status.HTTP_400_BAD_REQUEST)
            # Return user data using serializer
            serializer = UserSerializer(data={
                'registration_number': reg_number,
                'first_name': college_data.first_name,
                'last_name': college_data.last_name,
                'course': college_data.course.id
            })
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CollegeData.DoesNotExist:
            return Response({'error': 'Registration number not found'}, status=status.HTTP_404_NOT_FOUND)

class CompleteRegistrationView(APIView):
    """API endpoint to complete user registration with email, password, state, and course."""
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate input using serializer
        serializer = UserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        reg_number = request.data.get('registration_number')
        state_id = request.data.get('state')
        email = request.data.get('email', '').lower()
        password = request.data.get('password')
        course_id = request.data.get('course_id')

        if not all([reg_number, state_id, email, password, course_id]):
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            college_data = CollegeData.objects.get(registration_number=reg_number, is_used=False)
            state = State.objects.get(id=state_id)
            course = Course.objects.get(id=course_id)
            user, generated_password = User.objects.create_from_college_data(college_data.id)
            user.email = email
            user.state = state
            user.course = course
            user.set_password(password)
            user.is_verified = True
            user.date_verified = timezone.now()
            user.save()

            # Generate VoterToken for active elections
            active_elections = Election.objects.filter(is_active=True, has_ended=False)
            voter_tokens = []
            for election in active_elections:
                token = User.objects.generate_voter_token(user.id, election.id)
                voter_tokens.append({'election_title': election.title, 'token': str(token.token)})

            # Send verification email via Celery
            send_verification_email.delay(user.id, voter_tokens[0] if voter_tokens else None)

            return Response({
                'message': 'Registration successful, verification email sent',
                'voter_id': user.voter_id,
                'voter_tokens': voter_tokens
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            return Response({'error': 'Registration failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerificationRequestView(APIView):
    """API endpoint for users to request verification."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_verified:
            return Response({'message': 'User already verified'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            college_data = CollegeData.objects.get(registration_number=user.registration_number, is_used=True)
            college_data.status = 'pending'
            college_data.save()
            send_commissioner_contact_email.delay(
                user.id,
                f"Verification request for {user.registration_number}"
            )
            return Response({'message': 'Verification request submitted'}, status=status.HTTP_200_OK)
        except CollegeData.DoesNotExist:
            return Response({'error': 'College data not found'}, status=status.HTTP_404_NOT_FOUND)

class VerifyUserView(APIView):
    """API endpoint for commissioners to verify users."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.can_manage_elections():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        reg_number = request.data.get('registration_number')
        try:
            user = User.objects.get(registration_number=reg_number)
            if user.is_verified:
                return Response({'message': 'User already verified'}, status=status.HTTP_400_BAD_REQUEST)
            user.is_verified = True
            user.date_verified = timezone.now()
            user.save()

            # Generate VoterToken for active elections
            active_elections = Election.objects.filter(is_active=True, has_ended=False)
            voter_tokens = []
            for election in active_elections:
                token = User.objects.generate_voter_token(user.id, election.id)
                voter_tokens.append({'election_title': election.title, 'token': str(token.token)})

            # Send verification email via Celery
            send_verification_email.delay(user.id, voter_tokens[0] if voter_tokens else None)

            return Response({'message': 'User verified, email sent'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class VerificationStatusView(APIView):
    """API endpoint to check user verification status."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response({
            'is_verified': serializer.data['is_verified'],
            'date_verified': user.date_verified,
        }, status=status.HTTP_200_OK)

class ForgotPasswordView(APIView):
    """API endpoint for password reset with security questions."""
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate input using serializer
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        reg_number = serializer.validated_data['registration_number']
        email = serializer.validated_data['email'].lower()
        state_id = serializer.validated_data['state'].id
        course_id = serializer.validated_data['course'].id
        first_name = serializer.validated_data.get('first_name', '')
        last_name = serializer.validated_data.get('last_name', '')

        try:
            user = User.objects.get(
                registration_number=reg_number,
                email=email,
                state_id=state_id,
                course_id=course_id
            )
            if first_name and user.first_name != first_name:
                return Response({'error': 'First name does not match'}, status=status.HTTP_400_BAD_REQUEST)
            if last_name and user.last_name != last_name:
                return Response({'error': 'Last name does not match'}, status=status.HTTP_400_BAD_REQUEST)

            new_password = secrets.token_hex(8)
            user.set_password(new_password)
            user.save()
            send_password_reset_email.delay(user.id, new_password)
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found or details do not match'}, status=status.HTTP_404_NOT_FOUND)

class UserDashboardView(APIView):
    """API endpoint for user dashboard data."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ongoing_elections = Election.objects.filter(is_active=True, has_ended=False).values('id', 'title', 'start_date', 'end_date')
        upcoming_elections = Election.objects.filter(is_active=False, has_ended=False).values('id', 'title', 'start_date')
        past_elections = Election.objects.filter(has_ended=True).values('id', 'title', 'end_date')
        election_levels = ElectionLevel.objects.values('id', 'name', 'code')

        serializer = UserSerializer(request.user)
        return Response({
            'ongoing_elections': list(ongoing_elections),
            'upcoming_elections': list(upcoming_elections),
            'past_elections': list(past_elections),
            'election_levels': list(election_levels),
            'user': serializer.data
        }, status=status.HTTP_200_OK)

class ContactCommissionerView(APIView):
    """API endpoint to contact commissioners."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message_content = request.data.get('message')
        if not message_content:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        send_commissioner_contact_email.delay(request.user.id, message_content)
        return Response({'message': 'Message sent to commissioners'}, status=status.HTTP_200_OK)