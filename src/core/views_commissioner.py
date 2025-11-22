"""
Commissioner Dashboard Views
Provides comprehensive analytics and management capabilities for election commissioners.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, F
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import User, State, Course, CollegeData
from election.models import Election, ElectionLevel, Position, Candidate, Vote, VoterToken
from .permissions import IsCommissioner


@login_required
def commissioner_dashboard(request):
    """Main dashboard view for commissioners."""
    # Check if user is commissioner
    if request.user.role != User.ROLE_COMMISSIONER:
        messages.error(request, 'Access denied. Commissioners only.')
        return redirect('home')
    
    # Get overall statistics
    total_users = User.objects.count()
    verified_users = User.objects.filter(is_verified=True).count()
    pending_verification = User.objects.filter(is_verified=False).count()
    
    active_elections = Election.objects.filter(is_active=True, has_ended=False).count()
    total_elections = Election.objects.count()
    completed_elections = Election.objects.filter(has_ended=True).count()
    
    total_votes = Vote.objects.count()
    total_candidates = Candidate.objects.count()
    
    # Get recent elections
    recent_elections = Election.objects.all().order_by('-created_at')[:5]
    
    # Get voter participation by state
    state_stats = State.objects.annotate(
        total_voters=Count('user'),
        verified_voters=Count('user', filter=Q(user__is_verified=True))
    ).values('name', 'total_voters', 'verified_voters')
    
    # Get course statistics
    course_stats = Course.objects.annotate(
        total_students=Count('user'),
        verified_students=Count('user', filter=Q(user__is_verified=True))
    ).values('name', 'code', 'total_students', 'verified_students')[:10]
    
    # Get pending verifications
    pending_users = User.objects.filter(is_verified=False).select_related('course', 'state')[:10]
    
    context = {
        'total_users': total_users,
        'verified_users': verified_users,
        'pending_verification': pending_verification,
        'active_elections': active_elections,
        'total_elections': total_elections,
        'completed_elections': completed_elections,
        'total_votes': total_votes,
        'total_candidates': total_candidates,
        'recent_elections': recent_elections,
        'state_stats': list(state_stats),
        'course_stats': list(course_stats),
        'pending_users': pending_users,
    }
    
    return render(request, 'core/commissioner_dashboard.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCommissioner])
def dashboard_stats_api(request):
    """API endpoint for commissioner dashboard statistics."""
    stats = {
        'users': {
            'total': User.objects.count(),
            'verified': User.objects.filter(is_verified=True).count(),
            'pending': User.objects.filter(is_verified=False).count(),
            'commissioners': User.objects.filter(role=User.ROLE_COMMISSIONER).count(),
            'voters': User.objects.filter(role=User.ROLE_VOTER).count(),
        },
        'elections': {
            'total': Election.objects.count(),
            'active': Election.objects.filter(is_active=True, has_ended=False).count(),
            'completed': Election.objects.filter(has_ended=True).count(),
            'upcoming': Election.objects.filter(is_active=False, has_ended=False, start_date__gt=timezone.now()).count(),
        },
        'voting': {
            'total_votes': Vote.objects.count(),
            'total_candidates': Candidate.objects.count(),
            'total_positions': Position.objects.count(),
            'tokens_issued': VoterToken.objects.count(),
            'tokens_used': VoterToken.objects.filter(is_used=True).count(),
        },
        'participation': {
            'states': list(State.objects.annotate(
                voter_count=Count('user', filter=Q(user__is_verified=True))
            ).values('name', 'voter_count')),
            'courses': list(Course.objects.annotate(
                student_count=Count('user', filter=Q(user__is_verified=True))
            ).values('name', 'code', 'student_count')[:10]),
        }
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCommissioner])
def election_analytics_api(request, election_id):
    """Get detailed analytics for a specific election."""
    try:
        election = Election.objects.get(id=election_id)
    except Election.DoesNotExist:
        return Response({'error': 'Election not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get election levels and their statistics
    levels_data = []
    for level in election.levels.all():
        level_votes = Vote.objects.filter(election=election, election_level=level).count()
        level_tokens = VoterToken.objects.filter(election=election, election_level=level).count()
        level_tokens_used = VoterToken.objects.filter(election=election, election_level=level, is_used=True).count()
        
        levels_data.append({
            'id': level.id,
            'name': level.name,
            'type': level.type,
            'total_votes': level_votes,
            'tokens_issued': level_tokens,
            'tokens_used': level_tokens_used,
            'participation_rate': round((level_tokens_used / level_tokens * 100), 2) if level_tokens > 0 else 0,
        })
    
    # Get candidate statistics
    candidates = Candidate.objects.filter(election=election).select_related('user', 'position')
    candidates_data = []
    for candidate in candidates:
        vote_count = Vote.objects.filter(candidate=candidate).count()
        candidates_data.append({
            'id': candidate.id,
            'name': candidate.user.get_full_name(),
            'position': candidate.position.title,
            'votes': vote_count,
        })
    
    data = {
        'election': {
            'id': election.id,
            'title': election.title,
            'description': election.description,
            'start_date': election.start_date,
            'end_date': election.end_date,
            'is_active': election.is_active,
            'has_ended': election.has_ended,
        },
        'levels': levels_data,
        'candidates': candidates_data,
        'summary': {
            'total_votes': Vote.objects.filter(election=election).count(),
            'total_tokens_issued': VoterToken.objects.filter(election=election).count(),
            'total_tokens_used': VoterToken.objects.filter(election=election, is_used=True).count(),
            'total_candidates': candidates.count(),
        }
    }
    
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCommissioner])
def verify_user_api(request, user_id):
    """API endpoint to verify a user account."""
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if user.is_verified:
        return Response({'error': 'User already verified'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.is_verified = True
    user.date_verified = timezone.now()
    user.save()
    
    return Response({
        'message': 'User verified successfully',
        'user': {
            'id': user.id,
            'name': user.get_full_name(),
            'registration_number': user.registration_number,
            'email': user.email,
            'is_verified': user.is_verified,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCommissioner])
def pending_verifications_api(request):
    """Get list of users pending verification."""
    pending_users = User.objects.filter(is_verified=False).select_related('course', 'state')
    
    users_data = []
    for user in pending_users:
        users_data.append({
            'id': user.id,
            'registration_number': user.registration_number,
            'name': user.get_full_name(),
            'email': user.email,
            'course': user.course.name if user.course else None,
            'state': user.state.name if user.state else None,
            'date_joined': user.date_joined,
        })
    
    return Response({'pending_users': users_data, 'count': len(users_data)})
