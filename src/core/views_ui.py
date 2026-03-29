# core/views_ui.py
# Function-based views for Django session-based UI
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from .models import User, CollegeData, State, Course
from election.models import VoterToken, Election

logger = logging.getLogger(__name__)


def home(request):
    """Home/landing page view."""
    return render(request, 'core/landing.html')

def contributors_view(request):
    """Public contributors page - no login required."""
    return render(request, 'core/contributors.html')

@require_http_methods(["GET", "POST"])
def login_view(request):
    """Login view with Django session authentication."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        registration_number = request.POST.get('registration_number')
        password = request.POST.get('password')
        
        # Authenticate using the custom backend
        user = authenticate(request, registration_number=registration_number, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('core:dashboard')
        else:
            messages.error(request, 'Invalid registration number or password.')
    
    return render(request, 'core/login.html')


@login_required
def logout_view(request):
    """Logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:login')


@require_http_methods(["GET", "POST"])
def register_view(request):
    """Two-step registration view for new users.
    Step 1: Verify registration number in college data
    Step 2: Complete registration with email, password, state, etc.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        step = request.POST.get('step', '1')
        
        # STEP 1: Check registration number in college data
        if step == '1':
            registration_number = request.POST.get('registration_number', '').strip()
            
            if not registration_number:
                messages.error(request, 'Registration number is required.')
                return render(request, 'core/register.html', {'step': 1})
            
            try:
                # Check if college data exists and is not used
                college_data = CollegeData.objects.get(
                    registration_number=registration_number,
                    is_used=False
                )
                
                # Check if user already exists
                if User.objects.filter(registration_number=registration_number).exists():
                    messages.error(request, 'Registration number already registered.')
                    return render(request, 'core/register.html', {'step': 1})
                
                # College data found, proceed to step 2 with pre-filled info
                context = {
                    'step': 2,
                    'registration_number': college_data.registration_number,
                    'first_name': college_data.first_name,
                    'last_name': college_data.last_name,
                    'gender': college_data.gender,
                    'suggested_email': college_data.email if college_data.email else '',
                    'course_id': college_data.course.id if college_data.course else None,
                    'states': State.objects.all(),
                    'courses': Course.objects.all()
                }
                return render(request, 'core/register.html', context)
                
            except CollegeData.DoesNotExist:
                messages.error(request, 'Registration number not found or already used.')
                return render(request, 'core/register.html', {'step': 1})
        
        # STEP 2: Complete registration
        elif step == '2':
            registration_number = request.POST.get('registration_number')
            email = request.POST.get('email')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            state_id = request.POST.get('state')
            course_id = request.POST.get('course')
            
            # Validate all fields
            if not all([registration_number, email, password, password_confirm, state_id, course_id]):
                messages.error(request, 'All fields are required.')
                college_data = CollegeData.objects.get(registration_number=registration_number)
                context = {
                    'step': 2,
                    'registration_number': registration_number,
                    'first_name': college_data.first_name,
                    'last_name': college_data.last_name,
                    'gender': college_data.gender,
                    'states': State.objects.all(),
                    'courses': Course.objects.all()
                }
                return render(request, 'core/register.html', context)
            
            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                college_data = CollegeData.objects.get(registration_number=registration_number)
                context = {
                    'step': 2,
                    'registration_number': registration_number,
                    'first_name': college_data.first_name,
                    'last_name': college_data.last_name,
                    'gender': college_data.gender,
                    'states': State.objects.all(),
                    'courses': Course.objects.all()
                }
                return render(request, 'core/register.html', context)
            
            try:
                # Verify college data still valid
                college_data = CollegeData.objects.get(
                    registration_number=registration_number,
                    is_used=False
                )
                
                # Check email not already used
                if User.objects.filter(email=email.lower()).exists():
                    messages.error(request, 'Email already registered.')
                    context = {
                        'step': 2,
                        'registration_number': registration_number,
                        'first_name': college_data.first_name,
                        'last_name': college_data.last_name,
                        'gender': college_data.gender,
                        'states': State.objects.all(),
                        'courses': Course.objects.all()
                    }
                    return render(request, 'core/register.html', context)
                
                # Get state and course
                state = State.objects.get(id=state_id)
                course = Course.objects.get(id=course_id)
                
                # Create user from college data
                user, _ = User.objects.create_from_college_data(college_data.id)
                
                # Update user with provided details
                user.email = email.lower()
                user.state = state
                user.course = course
                user.set_password(password)
                user.save()
                
                # Mark college data as used
                college_data.is_used = True
                college_data.save()
                
                messages.success(request, 'Registration successful! Please log in.')
                return redirect('core:login')
                
            except CollegeData.DoesNotExist:
                messages.error(request, 'Registration number not found or already used.')
                return render(request, 'core/register.html', {'step': 1})
            except State.DoesNotExist:
                messages.error(request, 'Invalid state selected.')
                return render(request, 'core/register.html', {'step': 1})
            except Course.DoesNotExist:
                messages.error(request, 'Invalid course selected.')
                return render(request, 'core/register.html', {'step': 1})
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, 'Registration failed. Please try again.')
                return render(request, 'core/register.html', {'step': 1})
    
    # GET request - show step 1
    return render(request, 'core/register.html', {'step': 1})


@login_required
def dashboard_view(request):
    """User dashboard view with filtered elections and tokens."""
    user = request.user
    now = timezone.now()
    
    # Get user's voting tokens with election details
    tokens = VoterToken.objects.filter(user=user).select_related(
        'election', 'election_level'
    ).order_by('-election__start_date')
    
    # Get elections status
    active_elections = Election.objects.filter(is_active=True, has_ended=False).order_by('end_date')
    completed_elections = Election.objects.filter(has_ended=True).order_by('-end_date')
    upcoming_elections = Election.objects.filter(
        is_active=False,
        has_ended=False,
        start_date__gt=now
    ).order_by('start_date')[:5]
    
    # Process tokens to show status
    active_tokens = []
    completed_tokens = []
    
    for token in tokens:
        token_data = {
            'token': token,
            'status': 'used' if token.is_used else 'available',
            'is_active': token.election.is_active,
            'election_ended': token.election.has_ended,
        }
        
        if token.election.is_active:
            active_tokens.append(token_data)
        elif token.election.has_ended:
            completed_tokens.append(token_data)
    
    # Check profile edit eligibility
    can_edit_profile = not active_elections.exists()
    edit_status = 'restricted' if active_elections.exists() else 'allowed'
    
    context = {
        'user': user,
        'active_tokens': active_tokens,
        'completed_tokens': completed_tokens,
        'active_elections': active_elections,
        'completed_elections': completed_elections[:5],
        'upcoming_elections': upcoming_elections,
        'can_edit_profile': can_edit_profile,
        'profile_edit_status': edit_status,
        'total_tokens': tokens.count(),
        'used_tokens': tokens.filter(is_used=True).count(),
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit_view(request):
    """User profile edit view - allows editing email and gender when no election is active or 24 hours before start."""
    user = request.user
    now = timezone.now()
    
    # Check active elections (currently ongoing)
    active_elections = Election.objects.filter(is_active=True, has_ended=False)
    
    # Check upcoming elections (within 24 hours before start)
    upcoming_soon = Election.objects.filter(
        start_date__lte=now + timedelta(hours=24),
        start_date__gte=now,
        is_active=False,
        has_ended=False
    )
    
    # Can edit if:
    # 1. There are NO active elections AND
    # 2. Either there are no upcoming elections within 24 hours OR within the 24-hour window
    can_edit_email_gender = not active_elections.exists()
    edit_reason = None
    
    if can_edit_email_gender:
        if upcoming_soon.exists():
            edit_reason = "pre_election"  # Within 24 hours before election
        else:
            edit_reason = "no_election"  # No elections active or coming soon
    else:
        edit_reason = "election_active"  # Election is currently active
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        gender = request.POST.get('gender', '').strip()
        
        # Validate email if provided
        if email and email != user.email:
            # Check if email already exists
            if User.objects.filter(email=email.lower()).exclude(id=user.id).exists():
                messages.error(request, 'Email already registered.')
            else:
                # Only allow email/gender edits when allowed
                if can_edit_email_gender:
                    user.email = email.lower()
                    if gender and gender in dict(User.GENDER_CHOICES):
                        user.gender = gender
                    user.save()
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('core:dashboard')
                else:
                    messages.error(request, 'Profile editing is not available while an election is active.')
        elif gender and gender != user.gender:
            if can_edit_email_gender:
                if gender in dict(User.GENDER_CHOICES):
                    user.gender = gender
                    user.save()
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('core:dashboard')
                else:
                    messages.error(request, 'Invalid gender selected.')
            else:
                messages.error(request, 'Profile editing is not available while an election is active.')
        else:
            messages.info(request, 'No changes made.')
    
    # Get available courses and states for reference
    states = State.objects.all()
    courses = Course.objects.all()
    
    context = {
        'user': user,
        'states': states,
        'courses': courses,
        'can_edit_email_gender': can_edit_email_gender,
        'edit_reason': edit_reason,
        'active_elections': active_elections,
        'upcoming_elections': upcoming_soon,
        'gender_choices': User.GENDER_CHOICES,
    }
    
    return render(request, 'core/profile_edit.html', context)
