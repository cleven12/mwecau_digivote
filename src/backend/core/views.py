import secrets
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.conf import settings
from django.core.mail import send_mail

from core import serializers
from .models import User, CollegeData, State, Course
from election.models import Election, ElectionLevel, VoterToken
import logging
from celery import shared_task


logger = logging.getLogger(__name__)

# Celery tasks for email notifications
@shared_task(queue='email_queue')
def send_verification_email(user_id, voter_token=None):
    """Send verification email with user details and optional VoterToken."""
    user = User.objects.get(id=user_id)
    subject = "MWECAU Election Platform - Account Verification"
    message = (
        f"Dear {user.get_full_name()},\n\n"
        f"Your account has been verified:\n"
        f"- Registration Number: {user.registration_number}\n"
        f"- Email: {user.email}\n"
        f"- Course: {user.course.name if user.course else 'N/A'}\n"
        f"- State: {user.state.name if user.state else 'N/A'}\n"
        f"- Voter ID: {user.voter_id}\n"
    )
    if voter_token:
        message += f"- Voter Token for {voter_token.election.title}: {voter_token.token}\n"
    message += "Log in at http://localhost:8000/api/auth/login/ to participate in elections."
    send_mail( 
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=True,
    )

@shared_task(queue='email_queue')
def send_password_reset_email(user_id, new_password):
    """Send password reset email with new password."""
    user = User.objects.get(id=user_id)
    subject = "MWECAU Election Platform - Password Reset"
    message = (
        f"Dear {user.get_full_name()},\n\n"
        f"Your password has been reset:\n"
        f"- Registration Number: {user.registration_number}\n"
        f"- New Password: {new_password}\n"
        f"Log in at http://localhost:8000/api/auth/login/ with your new password."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[user.email],
        fail_silently=True,
    )

@shared_task(queue='email_queue')
def send_commissioner_contact_email(user_id, message_content):
    """Send contact message to commissioners."""
    user = User.objects.get(id=user_id)
    commissioners = User.objects.filter(role=User.ROLE_COMMISSIONER, is_verified=True)
    subject = "MWECAU Election Platform - User Contact Request"
    message = (
        f"Message from {user.get_full_name()} ({user.registration_number}):\n\n"
        f"{message_content}\n\n"
        f"Reply to: {user.email}"
    )
    recipient_list = [comm.email for comm in commissioners if comm.email]
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=recipient_list,
        fail_silently=True,
    )

# Custom serializer for JWT login with registration_number
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom serializer to use registration_number for JWT login."""
    def validate(self, attrs):
        registration_number = attrs.get('registration_number')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            registration_number=registration_number,
            password=password
        )
        if user is None:
            raise serializers.ValidationError('Invalid registration number or password')

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

# API Views
class UserLoginView(APIView):
    """API endpoint for user login with registration_number."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomTokenObtainPairSerializer(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class UserRegisterView(APIView):
    """API endpoint for user registration via CollegeData."""
    permission_classes = [AllowAny]

    def post(self, request):
        reg_number = request.data.get('registration_number', '').strip()
        try:
            college_data = CollegeData.objects.get(registration_number=reg_number)
            if User.objects.filter(registration_number=reg_number).exists():
                return Response({'error': 'Registration number already registered'}, status=status.HTTP_400_BAD_REQUEST)
            if college_data.is_used:
                return Response({'error': 'College data already used'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'registration_number': reg_number,
                'full_name': f"{college_data.first_name} {college_data.last_name}",
                'course_id': college_data.course.id
            }, status=status.HTTP_200_OK)
        except CollegeData.DoesNotExist:
            return Response({'error': 'Registration number not found'}, status=status.HTTP_404_NOT_FOUND)

class CompleteRegistrationView(APIView):
    """API endpoint to complete user registration."""
    permission_classes = [AllowAny]

    def post(self, request):
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

            # Send verification email
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
    """API endpoint to request user verification."""
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

            # Send verification email
            send_verification_email.delay(user.id, voter_tokens[0] if voter_tokens else None)

            return Response({'message': 'User verified, email sent'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class VerificationStatusView(APIView):
    """API endpoint to check verification status."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'is_verified': user.is_verified,
            'date_verified': user.date_verified,
        }, status=status.HTTP_200_OK)

class ForgotPasswordView(APIView):
    """API endpoint for password reset with security questions."""
    permission_classes = [AllowAny]

    def post(self, request):
        reg_number = request.data.get('registration_number')
        email = request.data.get('email', '').lower()
        state_id = request.data.get('state')
        course_id = request.data.get('course')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        if not all([reg_number, email, state_id, course_id]):
            return Response({'error': 'Registration number, email, state, and course are required'}, status=status.HTTP_400_BAD_REQUEST)

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

        return Response({
            'ongoing_elections': list(ongoing_elections),
            'upcoming_elections': list(upcoming_elections),
            'past_elections': list(past_elections),
            'election_levels': list(election_levels),
            'user': {
                'registration_number': request.user.registration_number,
                'full_name': request.user.get_full_name(),
                'is_verified': request.user.is_verified,
                'role': request.user.role
            }
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

# Non-API Views (retained for compatibility)
def index(request):
    """Home page view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/login.html')

def login_view(request):
    """Login view for the system."""
    if request.method == 'POST':
        email = request.POST.get('email', '').lower()
        password = request.POST.get('password', '')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'core/login.html')

def logout_view(request):
    """Logout view for the system."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

def register(request):
    """Registration view for new users."""
    if request.method == 'POST':
        reg_number = request.POST.get('registration_number', '').strip()
        
        if reg_number:
            try:
                college_data = CollegeData.objects.get(registration_number=reg_number)
                
                request.session['validated_reg_number'] = reg_number
                request.session['validated_name'] = f"{college_data.first_name} {college_data.last_name}"
                request.session['validated_course_id'] = college_data.course.id
                
                if User.objects.filter(registration_number=reg_number).exists():
                    messages.error(request, 'This registration number is already registered. Please login.')
                    return redirect('login')
                
                return redirect('complete_registration')
                
            except CollegeData.DoesNotExist:
                messages.error(request, 'Registration number not found in our database.')
        else:
            messages.error(request, 'Please enter a registration number.')
            
    return render(request, 'core/register.html')

def complete_registration(request):
    """View to complete registration with state and email."""
    if 'validated_reg_number' not in request.session:
        messages.error(request, 'Please validate your registration number first.')
        return redirect('register')
    
    if request.method == 'POST':
        state_id = request.POST.get('state')
        email = request.POST.get('email', '').lower()
        password = request.POST.get('password')
        
        if not state_id or not email or not password:
            messages.error(request, 'All fields are required.')
            return render(request, 'core/register.html', {'states': State.objects.all()})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')
            return render(request, 'core/register.html', {'states': State.objects.all()})
        
        try:
            state = State.objects.get(id=state_id)
            course = Course.objects.get(id=request.session['validated_course_id'])
            college_data = CollegeData.objects.get(registration_number=request.session['validated_reg_number'], is_used=False)
            user, generated_password = User.objects.create_from_college_data(college_data.id)
            user.email = email
            user.state = state
            user.course = course
            user.set_password(password)
            user.is_verified = True
            user.date_verified = timezone.now()
            user.save()

            # Send verification email
            active_elections = Election.objects.filter(is_active=True, has_ended=False)
            voter_tokens = []
            for election in active_elections:
                token = User.objects.generate_voter_token(user.id, election.id)
                voter_tokens.append({'election_title': election.title, 'token': str(token.token)})
            send_verification_email.delay(user.id, voter_tokens[0] if voter_tokens else None)
            
            login(request, user)
            del request.session['validated_reg_number']
            del request.session['validated_name']
            del request.session['validated_course_id']
            messages.success(request, f'Registration successful. Your voter ID is {user.voter_id}')
            return redirect('dashboard')
            
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            messages.error(request, 'An error occurred during registration. Please try again.')
    
    states = State.objects.all()
    course = Course.objects.get(id=request.session['validated_course_id'])
    
    return render(request, 'core/register.html', {
        'states': states,
        'full_name': request.session['validated_name'],
        'course': course,
        'step': 'complete_profile'
    })

@login_required
def dashboard(request):
    """Dashboard view for authenticated users."""
    ongoing_elections = Election.objects.filter(is_active=True, has_ended=False).order_by('end_date')
    upcoming_elections = Election.objects.filter(is_active=False, has_ended=False).order_by('start_date')
    past_elections = Election.objects.filter(has_ended=True).order_by('-end_date')
    election_levels = ElectionLevel.objects.all()
    
    context = {
        'ongoing_elections': ongoing_elections,
        'upcoming_elections': upcoming_elections,
        'past_elections': past_elections,
        'election_levels': election_levels,
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
def contact_commissioner(request):
    """View for users to contact the election commissioner."""
    return render(request, 'core/contact_commissioner.html')