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

# Import your serializers and models
from core import serializers
from .models import User, CollegeData, State, Course
from .serializers import UserSerializer, ForgotPasswordSerializer
# Note: Election imports removed from UserDashboardView logic
# from election.models import Election, ElectionLevel, VoterToken 
from .tasks import send_verification_email, send_password_reset_email, send_commissioner_contact_email

logger = logging.getLogger(__name__)

# --- API Views ---

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
            # --- Key Change Here ---
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
            # --- End Key Change ---

            # Prepare data for UserSerializer validation (email can be optional initially)
            email = college_data.email if college_data.email and college_data.email.strip() else None
            
            # --- Key Change: Prepare data for the *response*, not just the serializer ---
            # Use the fetched course_name directly in the response data
            response_data = {
                'registration_number': reg_number,
                'first_name': college_data.first_name,
                'last_name': college_data.last_name,
                # 'email': email, # Optional: Omit if null/empty as per desired response
                # 'is_verified': False, # Not needed in pre-check response
                # 'role': 'voter', # Not needed in pre-check response
                'course': {
                    'id': course.pk,       # Include Course ID
                    'name': course_name    # Include Course Name
                }
            }

            # Validate the data structure using the serializer (without saving)
            serializer_data_for_validation = {
                 'registration_number': reg_number,
                 'first_name': college_data.first_name,
                 'last_name': college_data.last_name,
                 'email': email,
                 'is_verified': False,
                 'role': 'voter',
                 'course': course.pk # Use course ID for validation (as before)
            }
            # v[01]
            # response_data = {
            #     'registration_number': reg_number,
            #     'first_name': college_data.first_name,
            #     'last_name': college_data.last_name,
            #     # 'email': email, # Optional: Omit if null/empty as per desired response
            #     # 'is_verified': False, # Not needed in pre-check response
            #     # 'role': 'voter', # Not needed in pre-check response
            #     'course': course_name # Use the fetched course name
            # }
            
            # # Validate the data structure using the serializer (without saving)
            # serializer_data_for_validation = {
            #      'registration_number': reg_number,
            #      'first_name': college_data.first_name,
            #      'last_name': college_data.last_name,
            #      'email': email,
            #      'is_verified': False,
            #      'role': 'voter',
            #      'course': course.pk # Use course ID for validation
            # }
            
            logger.debug(f"Serializer data for validation: {serializer_data_for_validation}")
            serializer = UserSerializer(data=serializer_data_for_validation)
            if serializer.is_valid():
                logger.debug(f"Serializer valid")
                # --- Key Change: Return the manually constructed response_data ---
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
        # Validate input using serializer FIRST
        # The serializer handles converting course ID to course object
        serializer = UserSerializer(data=request.data) 
        if not serializer.is_valid():
            logger.error(f"CompleteRegistration serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # If valid, extract validated data
        reg_number = serializer.validated_data.get('registration_number')
        # Note: serializer.validated_data['course'] is now a Course object due to to_internal_value
        # But we still need state and password from request.data as they are not in UserSerializer
        state_id = request.data.get('state') 
        email = request.data.get('email', '').lower()
        password = request.data.get('password')
        # Get course_id from the validated data if needed, or use request.data
        # It's safer to get it from request.data since it's what the client sent
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
            # IMPORTANT: Use the provided password, not the generated one
            user.set_password(password) 
            user.is_verified = True # Mark as verified upon completion
            user.date_verified = timezone.now()
            user.save()
            logger.debug("User details updated and saved")

            # 5. Send welcome email WITHOUT voter tokens (as per updated logic)
            # Pass only user ID to the task
            send_verification_email.delay(user.id) 
            logger.debug("Verification email task queued")

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
                # 'voter_tokens': [] # Removed voter tokens from registration response
            }, status=status.HTTP_201_CREATED)
            
        except CollegeData.DoesNotExist:
             logger.error(f"CompleteRegistration: College data for {reg_number} not found or already used")
             return Response({'error': 'College data not found or already used'}, status=status.HTTP_404_NOT_FOUND)
        except (State.DoesNotExist, Course.DoesNotExist) as e:
             logger.error(f"CompleteRegistration: Invalid state or course ID provided: {e}")
             return Response({'error': 'Invalid state or course selected'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e: # Catch other potential errors during user creation/update
            logger.error(f"Error during CompleteRegistration for {reg_number}: {str(e)}", exc_info=True) # Log full traceback
            return Response({'error': 'Registration completion failed. Please try again or contact support.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# v[01]
# class CompleteRegistrationView(APIView):
#     """API endpoint to complete user registration with email, password, state, and course."""
#     permission_classes = [AllowAny]

#     def post(self, request):
#         serializer = UserSerializer(data=request.data)
#         if not serializer.is_valid():
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#         reg_number = request.data.get('registration_number')
#         state_id = request.data.get('state') # Expecting state ID
#         email = request.data.get('email', '').lower()
#         password = request.data.get('password')
#         course_id = request.data.get('course') # Expecting course ID

#         if not all([reg_number, state_id, email, password, course_id]):
#             return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

#         if User.objects.filter(email=email).exists():
#             return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             college_data = CollegeData.objects.get(registration_number=reg_number, is_used=False)
#             state = State.objects.get(id=state_id)
#             course = Course.objects.get(id=course_id)
            
#             # Create user using the manager method
#             user, generated_password = User.objects.create_from_college_data(college_data.id)
#             user.email = email
#             user.state = state
#             user.course = course
#             user.set_password(password) # Use provided password, not generated one
#             user.is_verified = True
#             user.date_verified = timezone.now()
#             user.save()

#             # Send welcome email WITHOUT voter tokens (as per updated logic)
#             send_verification_email.delay(user.id) # Pass only user ID

#             return Response({
#                 'message': 'Registration successful, welcome email sent',
#                 'voter_id': user.voter_id,
#                 # 'voter_tokens': [] # Removed voter tokens from registration response
#             }, status=status.HTTP_201_CREATED)
#         except CollegeData.DoesNotExist:
#              return Response({'error': 'College data not found or already used'}, status=status.HTTP_404_NOT_FOUND)
#         except (State.DoesNotExist, Course.DoesNotExist):
#              return Response({'error': 'Invalid state or course selected'}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Error during registration: {str(e)}")
#             return Response({'error': 'Registration failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerificationRequestView(APIView):
    """API endpoint for users to request verification."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_verified:
            return Response({'message': 'User already verified'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Assuming CollegeData needs to be re-verified or status updated
            college_data = CollegeData.objects.get(registration_number=user.registration_number, is_used=True)
            # Example: Update status to pending review
            college_data.status = 'pending' 
            college_data.save()
            # Notify commissioners
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

            # Send welcome email WITH voter tokens IF elections are active
            # This task will handle checking for active elections internally
            send_verification_email.delay(user.id) # Pass only user ID

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
            # Optional: Add name verification if required by security policy
            # if first_name and user.first_name != first_name:
            #     return Response({'error': 'First name does not match'}, status=status.HTTP_400_BAD_REQUEST)
            # if last_name and user.last_name != last_name:
            #     return Response({'error': 'Last name does not match'}, status=status.HTTP_400_BAD_REQUEST)

            new_password = secrets.token_hex(8)
            user.set_password(new_password)
            user.save()
            send_password_reset_email.delay(user.id, new_password)
            return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found or details do not match'}, status=status.HTTP_404_NOT_FOUND)

# --- Simplified Dashboard ---
class UserDashboardView(APIView):
    """API endpoint for user dashboard data - Simplified."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Return only a simple welcome message and basic user info
        return Response({
            'message': 'Welcome to the MWECAU Digital Voting System!',
            'status': 'authenticated',
            'user': {
                'registration_number': request.user.registration_number,
                'full_name': request.user.get_full_name(),
                'role': request.user.role,
                'course': request.user.course.name if request.user.course else None,
                'state': request.user.state.name if request.user.state else None,
            }
        }, status=status.HTTP_200_OK)

# --- Contact Form ---
class ContactCommissionerView(APIView):
    """API endpoint to contact commissioners."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message_content = request.data.get('message')
        if not message_content:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        # Send message via Celery task
        send_commissioner_contact_email.delay(request.user.id, message_content)
        return Response({'message': 'Message sent to commissioners'}, status=status.HTTP_200_OK)
