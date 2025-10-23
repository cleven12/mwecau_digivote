from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.utils.crypto import get_random_string
from django.db import transaction
import csv
from io import TextIOWrapper

from .models import User, State, Course, CollegeData
from .serializers import (
    UserSerializer, UserCreateSerializer, StateSerializer,
    CourseSerializer, LoginSerializer, VerifyRegistrationSerializer,
    CollegeDataSerializer, BulkCollegeDataUploadSerializer,
    PasswordChangeSerializer
)
from .permissions import IsClassLeader, IsCommissioner


class StateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing states.
    Read-only access for all authenticated users.
    """
    queryset = State.objects.all().order_by('name')
    serializer_class = StateSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name']
    ordering_fields = ['name']


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing courses.
    Read-only access for all authenticated users.
    """
    queryset = Course.objects.all().order_by('code')
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'code']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing users.
    Commissioners can view all users.
    Regular users can only view their own profile.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['email', 'registration_number', 'first_name', 'last_name']
    filterset_fields = ['role', 'state', 'course', 'is_verified']
    ordering_fields = ['email', 'registration_number', 'date_joined']
    
    def get_queryset(self):
        """Filter queryset based on user role."""
        user = self.request.user
        
        if user.role == User.ROLE_COMMISSIONER:
            return User.objects.all()
        
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile."""
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_registration(request):
    """
    Verify registration number before account creation.
    Returns student details if registration number is valid.
    """
    serializer = VerifyRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        reg_number = serializer.validated_data['registration_number']
        
        try:
            college_data = CollegeData.objects.select_related('course').get(
                registration_number=reg_number
            )
            
            return Response({
                'status': 'success',
                'message': 'Registration number verified.',
                'data': {
                    'registration_number': college_data.registration_number,
                    'full_name': college_data.full_name,
                    'course': CourseSerializer(college_data.course).data
                }
            }, status=status.HTTP_200_OK)
            
        except CollegeData.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Registration number not found.'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'status': 'error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user account.
    Generates voter ID automatically.
    """
    serializer = UserCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                reg_number = serializer.validated_data['registration_number']
                college_data = CollegeData.objects.get(
                    registration_number=reg_number
                )
                
                voter_id = 'V' + get_random_string(
                    length=10,
                    allowed_chars='0123456789'
                )
                
                user = serializer.save(
                    voter_id=voter_id,
                    is_verified=True,
                    role=User.ROLE_VOTER
                )
                
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'status': 'success',
                    'message': 'Registration successful.',
                    'data': {
                        'user': UserSerializer(user).data,
                        'voter_id': voter_id,
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token),
                        }
                    }
                }, status=status.HTTP_201_CREATED)
                
        except CollegeData.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Registration number not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Registration failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'status': 'error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return JWT tokens.
    """
    serializer = LoginSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'status': 'success',
            'message': 'Login successful.',
            'data': {
                'user': UserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'status': 'error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting their refresh token.
    """
    try:
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'status': 'error',
                'message': 'Refresh token is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response({
            'status': 'success',
            'message': 'Logout successful.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Logout failed: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password.
    """
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'status': 'success',
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'status': 'error',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


class CollegeDataViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing college data.
    Only class leaders and commissioners can access.
    """
    queryset = CollegeData.objects.all().select_related('course')
    serializer_class = CollegeDataSerializer
    permission_classes = [IsAuthenticated, IsClassLeader | IsCommissioner]
    search_fields = ['registration_number', 'full_name']
    filterset_fields = ['course']
    ordering_fields = ['registration_number', 'full_name']
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Bulk upload college data from CSV file.
        Expected CSV format: registration_number, full_name, course_code, course_name
        """
        serializer = BulkCollegeDataUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = request.FILES['file']
        
        try:
            csv_file_wrapper = TextIOWrapper(
                csv_file.file,
                encoding='utf-8'
            )
            reader = csv.DictReader(csv_file_wrapper)
            
            required_columns = ['registration_number', 'full_name', 'course_code']
            for column in required_columns:
                if column not in reader.fieldnames:
                    return Response({
                        'status': 'error',
                        'message': f'CSV is missing required column: {column}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            students_added = 0
            students_updated = 0
            errors = []
            
            with transaction.atomic():
                for row in reader:
                    try:
                        reg_number = row['registration_number'].strip()
                        full_name = row['full_name'].strip()
                        course_code = row['course_code'].strip()
                        
                        course, _ = Course.objects.get_or_create(
                            code=course_code,
                            defaults={'name': row.get('course_name', course_code)}
                        )
                        
                        _, created = CollegeData.objects.update_or_create(
                            registration_number=reg_number,
                            defaults={
                                'full_name': full_name,
                                'course': course
                            }
                        )
                        
                        if created:
                            students_added += 1
                        else:
                            students_updated += 1
                            
                    except Exception as e:
                        errors.append(f"Row error: {str(e)}")
            
            return Response({
                'status': 'success',
                'message': 'Upload completed.',
                'data': {
                    'students_added': students_added,
                    'students_updated': students_updated,
                    'errors_count': len(errors),
                    'errors': errors[:10]
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Upload failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
