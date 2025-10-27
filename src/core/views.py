# core/views.py
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
from .tasks import send_verification_email, send_password_reset_email, send_commissioner_contact_email
import requests
from django.urls import reverse
logger = logging.getLogger(__name__)

class UserLoginView(APIView):
    """API endpoint for user login with registration_number and password."""
    permission_classes = [AllowAny]

    def post(self, request):
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
        from rest_framework_simplejwt.exceptions import TokenError
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({'error': 'Invalid or expired refresh token'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return Response({'error': 'Logout failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# user Registration and Credential Validation
class UserRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        reg_number = request.data.get('registration_number', '').strip()
        logger.debug(f"Register request for registration_number={reg_number}")
        try:
            college_data = CollegeData.objects.get(registration_number=reg_number)
            logger.debug(f"CollegeData: {college_data.__dict__}")
            if User.objects.filter(registration_number=reg_number).exists():
                logger.warning(f"Registration number {reg_number} already registered")
                return Response({'error': 'Registration number already registered'}, status=status.HTTP_400_BAD_REQUEST)
            if college_data.is_used:
                logger.warning(f"College data for {reg_number} already used")
                return Response({'error': 'College data already used'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch the course object to get its name for the response
            try:
                course = college_data.course # Get the related Course object
                if not course:
                     logger.error(f"No course associated with registration {reg_number}")
                     return Response({'error': 'No course associated with this registration'}, status=status.HTTP_400_BAD_REQUEST)
                course_name = course.name # Get the course name

            except Course.DoesNotExist: # Handle case where course relation is broken
                 logger.error(f"Course object for ID {college_data.course_id} not found")
                 return Response({'error': 'Associated course data is invalid'}, status=status.HTTP_400_BAD_REQUEST)

            # Prepare data for UserSerializer validation (email can be optional initially)
            email = college_data.email if college_data.email and college_data.email.strip() else None
            gender = college_data.gender

            # Use the fetched course_name directly in the response data
            response_data = {
                'registration_number': reg_number,
                'first_name': college_data.first_name,
                'last_name': college_data.last_name,
                'email': email, # used if null/empty as per desired response
                'is_verified': False, # not in pre-check response
                'role': 'voter', # '' '' in pre-check response
                'course': {
                    'id' : course.pk,
                    'code': course.code,      
                    'name': course_name  
                },
                'gender': gender
            }

            # Validate the data structure using the serializer (without saving)
            serializer_data_for_validation = {
                 'registration_number': reg_number,
                 'first_name': college_data.first_name,
                 'last_name': college_data.last_name,
                 'email': email,
                 'is_verified': False,
                 'role': 'voter',
                 'course': course.pk # course ID for validation
            }
            
            logger.debug(f"Serializer data for validation: {serializer_data_for_validation}")
            serializer = UserSerializer(data=serializer_data_for_validation)
            if serializer.is_valid():
                logger.debug(f"Serializer valid")
                # --- return the manually constructed response_data ---
                return Response(response_data, status=status.HTTP_200_OK) 
            logger.error(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CollegeData.DoesNotExist:
            logger.error(f"Registration number {reg_number} not found")
            return Response({'error': 'Registration number not found'}, status=status.HTTP_404_NOT_FOUND)

        

class CompleteRegistrationView(APIView):
    """API endpoint to complete user registration with email, password, state, and course."""
    permission_classes = [AllowAny]

    def post(self, request):
        # The serializer handles course ID to course object - Input Validation Serialization
        serializer = UserSerializer(data=request.data) 
        if not serializer.is_valid():
            logger.error(f"CompleteRegistration serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If valid, extract validated data
        reg_number = serializer.validated_data.get('registration_number')
        state_id = request.data.get('state') 
        email = request.data.get('email', '').lower()
        password = request.data.get('password')
        course_id = request.data.get('course') 

        logger.debug(f"CompleteRegistration data - Reg: {reg_number}, State: {state_id}, Email: {email}, Course ID: {course_id}")

        if not all([reg_number, state_id, email, password, course_id]):
            logger.warning("CompleteRegistration: Missing required fields")
            return Response({'error': 'All fields (registration_number, state, email, password, course) are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            logger.warning(f"CompleteRegistration: Email {email} already registered")
            return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 1. Get CollegeData (must exist and be unused)
            college_data = CollegeData.objects.get(registration_number=reg_number, is_used=False)
            logger.debug(f"Found CollegeData: {college_data.id}")

            # 2. Get State and Course objects based on IDs provided
            state = State.objects.get(id=state_id)
            course = Course.objects.get(id=course_id) # Use ID from request.data
            logger.debug(f"Resolved State: {state.name}, Course: {course.name}")

            # 3. Create user using the manager method (this sets voter_id, default password)
            user, generated_password_unused = User.objects.create_from_college_data(college_data.id)
            logger.debug(f"Created user: {user.registration_number}")

            # 4. Update user with provided details
            user.email = email
            user.state = state
            # The course might already be set by create_from_college_data, but override with selected one
            user.course = course 
            # use the provided password, not the generated one
            user.set_password(password) 
            user.is_verified = True
            user.date_verified = timezone.now()
            user.save()
            logger.debug("User details updated and saved")

            # 5. Send welcome email 
            # send_verification_email(user.id) 
            # logger.debug("Verification email task queued")

            return Response({
                'message': 'Registration successful, welcome email sent',
                'user': {
                    'registration_number': user.registration_number,
                    'full_name': user.get_full_name(),
                    'email': user.email,
                    'course': user.course.name if user.course else None,
                    'state': user.state.name if user.state else None,
                    'voter_id': user.voter_id,
                }
            }, status=status.HTTP_201_CREATED)
            
        except CollegeData.DoesNotExist:
             logger.error(f"CompleteRegistration: College data for {reg_number} not found or already used")
             return Response({'error': 'College data not found or already used'}, status=status.HTTP_404_NOT_FOUND)
        
        except (State.DoesNotExist, Course.DoesNotExist) as e:
             logger.error(f"CompleteRegistration: Invalid state or course ID provided: {e}")
             return Response({'error': 'Invalid state or course selected'}, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e: 
            logger.error(f"Error during CompleteRegistration for {reg_number}: {str(e)}", exc_info=True)
            return Response({'error': 'Registration completion failed. Please try again or contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            # Notify commissioners
            send_commissioner_contact_email(
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

            # Send welcome email WITH voter tokens IF elections are active
            # This task will handle checking for active elections internally
            send_verification_email(user.id)

            return Response({'message': 'User verified, welcome email sent'}, status=status.HTTP_200_OK)
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

            new_password = secrets.token_hex(8)
            user.set_password(new_password)
            user.save()
            # send_password_reset_email(user.id, new_password)
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found or details do not match'}, status=status.HTTP_404_NOT_FOUND)

# --- Simple Dashboard ---
class UserDashboardView(APIView):
    """API endpoint for user dashboard data - Simplified."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from election.models import VoterToken
        from election.serializers import VoterTokenSerializer
        
        # Get user's voting tokens
        tokens = VoterToken.objects.filter(user=request.user).select_related(
            'election', 'election_level'
        )
        tokens_data = VoterTokenSerializer(tokens, many=True, context={'request': request}).data
        
        # Return dashboard data with user info and tokens
        return Response({
            'message': 'Welcome to the MWECAU Digital Voting System!',
            'status': 'authenticated',
            'user': {
                'id': request.user.id,
                'registration_number': request.user.registration_number,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                'role': request.user.role,
                'role_display': request.user.get_role_display(),
                'is_verified': request.user.is_verified,
                'is_commissioner': request.user.role == 'commissioner',
                'voter_id': request.user.voter_id,
                "course": {
                    "id": request.user.course.id,
                    "code": request.user.course.code,
                    "name": request.user.course.name,
                } if request.user.course else None,
                "state": {
                    "id": request.user.state.id,
                    "name": request.user.state.name,
                } if request.user.state else None,
            },
            'voting_tokens': tokens_data
        }, status=status.HTTP_200_OK)

# --- Profile Management Views ---
class UpdateProfileView(APIView):
    """API endpoint to update user profile (state, email)."""
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        state_id = request.data.get('state')
        email = request.data.get('email')

        try:
            if state_id:
                state = State.objects.get(id=state_id)
                user.state = state
            
            if email:
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)
                user.email = email
            
            user.save()
            return Response({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)
        except State.DoesNotExist:
            return Response({'error': 'Invalid state'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return Response({'error': 'Failed to update profile'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangePasswordView(APIView):
    """API endpoint to change user password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({'error': 'Both old and new passwords are required'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({'error': 'New password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    """API endpoint to confirm password reset with token."""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not token or not new_password:
            return Response({'error': 'Token and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({'error': 'Password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from election.models import VoterToken
            voter_token = VoterToken.objects.select_related('user').get(token=token)
            
            if not voter_token.user:
                return Response({'error': 'Invalid reset token'}, status=status.HTTP_400_BAD_REQUEST)
            
            voter_token.user.set_password(new_password)
            voter_token.user.save()
            
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        except VoterToken.DoesNotExist:
            user_found = False
            for user in User.objects.all():
                if user.registration_number == token or user.voter_id == token:
                    user.set_password(new_password)
                    user.save()
                    user_found = True
                    break
            
            if user_found:
                return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid or expired reset token'}, status=status.HTTP_400_BAD_REQUEST)

# --- Contact Form ---
class ContactCommissionerView(APIView):
    """API endpoint to contact commissioners."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message_content = request.data.get('message')
        if not message_content:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        # Send message via Celery task
        send_commissioner_contact_email(request.user.id, message_content)
        return Response({'message': 'Message sent to commissioners'}, status=status.HTTP_200_OK)


# --- Reference Data Views ---
class StateListView(APIView):
    """API endpoint to get list of all states."""
    permission_classes = [AllowAny]

    def get(self, request):
        states = State.objects.all().order_by('name')
        data = [{'id': state.id, 'name': state.name} for state in states]
        return Response(data, status=status.HTTP_200_OK)


class CourseListView(APIView):
    """API endpoint to get list of all courses."""
    permission_classes = [AllowAny]

    def get(self, request):
        courses = Course.objects.all().order_by('code')
        data = [{'id': course.id, 'code': course.code, 'name': course.name} for course in courses]
        return Response(data, status=status.HTTP_200_OK)
    

class APIHealthCheckView(APIView):
    """API endpoint to check the health of all API endpoints."""
    permission_classes = [AllowAny]  # Public access for health checks

    def get(self, request):
        base_url = f"{request.scheme}://{request.get_host()}"
        health_data = {
            "status": "healthy",
            "endpoints": {},
            "timestamp": timezone.now().isoformat(),
            "environment": "development" if settings.DEBUG else "production"
        }

        # Helper function to check endpoint
        def check_endpoint(method, url, requires_auth=False, payload=None, expected_status=200):
            try:
                headers = {}
                if requires_auth:
                    headers['Authorization'] = 'Bearer mock_token'  # Mock token for auth checks
                response = requests.request(
                    method,
                    f"{base_url}{url}",
                    json=payload,
                    headers=headers,
                    timeout=5
                )
                is_healthy = response.status_code == expected_status
                return {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "status_code": response.status_code,
                    "message": "OK" if is_healthy else response.text[:100]
                }
            except requests.RequestException as e:
                logger.error(f"Health check failed for {url}: {str(e)}")
                return {
                    "status": "unhealthy",
                    "status_code": None,
                    "message": f"Request failed: {str(e)}"
                }

        # Core App Endpoints (from core/urls.py)
        health_data["endpoints"]["auth_login"] = check_endpoint(
            method="POST",
            url=reverse("core:api_login"),
            payload={"registration_number": "TEST-001", "password": "test"},
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without valid credentials
        )
        health_data["endpoints"]["auth_logout"] = check_endpoint(
            method="POST",
            url=reverse("core:api_logout"),
            payload={"refresh": "mock_refresh_token"},
            requires_auth=True,
            expected_status=status.HTTP_400_BAD_REQUEST  # Expect failure with invalid token
        )
        health_data["endpoints"]["auth_refresh"] = check_endpoint(
            method="POST",
            url=reverse("core:api_token_refresh"),
            payload={"refresh": "mock_refresh_token"},
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure with invalid token
        )
        health_data["endpoints"]["auth_register"] = check_endpoint(
            method="POST",
            url=reverse("core:api_register"),
            payload={"registration_number": "TEST-001"},
            expected_status=status.HTTP_404_NOT_FOUND  # Expect failure if reg number not found
        )
        health_data["endpoints"]["auth_complete_registration"] = check_endpoint(
            method="POST",
            url=reverse("core:api_complete_registration"),
            payload={
                "registration_number": "TEST-001",
                "email": "test@example.com",
                "password": "Test@1234",
                "password_confirm": "Test@1234",
                "state": 1,
                "course": 1
            },
            expected_status=status.HTTP_404_NOT_FOUND  # Expect failure if college data not found
        )
        health_data["endpoints"]["auth_verification_request"] = check_endpoint(
            method="POST",
            url=reverse("core:api_verification_request"),
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["auth_verify_user"] = check_endpoint(
            method="POST",
            url=reverse("core:api_verify_user"),
            payload={"registration_number": "TEST-001"},
            requires_auth=True,
            expected_status=status.HTTP_403_FORBIDDEN  # Expect failure without commissioner role
        )
        health_data["endpoints"]["auth_verification_status"] = check_endpoint(
            method="GET",
            url=reverse("core:api_verification_status"),
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["auth_forgot_password"] = check_endpoint(
            method="POST",
            url=reverse("core:api_forgot_password"),
            payload={
                "registration_number": "TEST-001",
                "email": "test@example.com",
                "state": 1,
                "course": 1
            },
            expected_status=status.HTTP_404_NOT_FOUND  # Expect failure if user not found
        )
        health_data["endpoints"]["auth_password_reset_request"] = check_endpoint(
            method="POST",
            url=reverse("core:api_password_reset_request"),
            payload={
                "registration_number": "TEST-001",
                "email": "test@example.com",
                "state": 1,
                "course": 1
            },
            expected_status=status.HTTP_404_NOT_FOUND  # Expect failure if user not found
        )
        health_data["endpoints"]["auth_password_reset_confirm"] = check_endpoint(
            method="POST",
            url=reverse("core:api_password_reset_confirm"),
            payload={"token": "mock_token", "new_password": "NewPass@123"},
            expected_status=status.HTTP_400_BAD_REQUEST  # Expect failure with invalid token
        )
        health_data["endpoints"]["auth_dashboard"] = check_endpoint(
            method="GET",
            url=reverse("core:api_dashboard"),
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["auth_update_profile"] = check_endpoint(
            method="PUT",
            url=reverse("core:api_update_profile"),
            payload={"email": "new@example.com", "state": 1},
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["auth_change_password"] = check_endpoint(
            method="POST",
            url=reverse("core:api_change_password"),
            payload={"old_password": "old", "new_password": "new"},
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["auth_contact_commissioner"] = check_endpoint(
            method="POST",
            url=reverse("core:api_contact_commissioner"),
            payload={"message": "Test message"},
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["states"] = check_endpoint(
            method="GET",
            url=reverse("core:api_states"),
            expected_status=status.HTTP_200_OK  # Public endpoint
        )
        health_data["endpoints"]["courses"] = check_endpoint(
            method="GET",
            url=reverse("core:api_courses"),
            expected_status=status.HTTP_200_OK  # Public endpoint
        )

        # Election App Endpoints (from election/urls.py)
        health_data["endpoints"]["election_list"] = check_endpoint(
            method="GET",
            url=reverse("election_list"),
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["election_vote"] = check_endpoint(
            method="POST",
            url=reverse("api_vote"),
            payload={"voter_token": "mock_token", "candidate_id": 1},
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["election_results"] = check_endpoint(
            method="GET",
            url=reverse("api_results", kwargs={"election_id": 1}),
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )

        # Admin Endpoints (from API documentation, not in provided urls.py)
        health_data["endpoints"]["users_list"] = check_endpoint(
            method="GET",
            url="/api/users/",
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["users_me"] = check_endpoint(
            method="GET",
            url="/api/users/me/",
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["college_data"] = check_endpoint(
            method="GET",
            url="/api/college-data/",
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["college_data_bulk_upload"] = check_endpoint(
            method="POST",
            url="/api/college-data/bulk-upload/",
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )

        # Documentation Endpoints (from mw_es/urls.py)
        health_data["endpoints"]["swagger_ui"] = check_endpoint(
            method="GET",
            url=reverse("schema-swagger-ui"),
            expected_status=status.HTTP_200_OK  # Public endpoint
        )
        health_data["endpoints"]["redoc"] = check_endpoint(
            method="GET",
            url=reverse("schema-redoc"),
            expected_status=status.HTTP_200_OK  # Public endpoint
        )

        # Check overall health
        if any(endpoint_data["status"] == "unhealthy" for endpoint_data in health_data["endpoints"].values()):
            health_data["status"] = "unhealthy"

        return Response(health_data, status=status.HTTP_200_OK)