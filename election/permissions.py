from rest_framework import permissions
from django.utils import timezone
from .models import Election


class IsElectionActive(permissions.BasePermission):
    """Permission class to check if election is active."""
    
    message = "This election is not currently active."
    
    def has_object_permission(self, request, view, obj):
        """Check if election is active and within voting period."""
        if isinstance(obj, Election):
            election = obj
        elif hasattr(obj, 'election'):
            election = obj.election
        else:
            return False
        
        now = timezone.now()
        return (
            election.is_active and
            not election.has_ended and
            election.start_date <= now <= election.end_date
        )


class HasNotVotedForPosition(permissions.BasePermission):
    """Permission class to check if user hasn't voted for a position yet."""
    
    message = "You have already voted for this position."
    
    def has_permission(self, request, view):
        """Basic authentication check."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user has already voted for this position."""
        from .models import Vote, Candidate
        
        if not isinstance(obj, Candidate):
            return False
        
        user = request.user
        candidate = obj
        
        return not Vote.objects.filter(
            voter=user,
            candidate__election=candidate.election,
            candidate__position=candidate.position
        ).exists()


class CanViewResults(permissions.BasePermission):
    """Permission class to check if user can view election results."""
    
    message = "Results are not available yet or you don't have permission to view them."
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user can view results.
        Commissioners can always view. Others can view after election ends.
        """
        from core.models import User
        from .models import Election
        
        user = request.user
        
        if user.role == User.ROLE_COMMISSIONER:
            return True
        
        if isinstance(obj, Election):
            return obj.has_ended
        
        return False


class IsCandidateInElection(permissions.BasePermission):
    """Permission class to check if user is a candidate in the election."""
    
    message = "You are not a candidate in this election."
    
    def has_object_permission(self, request, view, obj):
        """Check if user is a candidate in this election."""
        from .models import Election, Candidate
        
        user = request.user
        
        if isinstance(obj, Election):
            election = obj
        elif hasattr(obj, 'election'):
            election = obj.election
        else:
            return False
        
        return Candidate.objects.filter(
            user=user,
            election=election
        ).exists()


class CanManageElection(permissions.BasePermission):
    """Permission class for election management (create, update, delete)."""
    
    message = "Only commissioners can manage elections."
    
    def has_permission(self, request, view):
        """Check if user is a commissioner."""
        from core.models import User
        
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == User.ROLE_COMMISSIONER
        )
    
    def has_object_permission(self, request, view, obj):
        """Commissioners can manage any election."""
        from core.models import User
        
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == User.ROLE_COMMISSIONER
        )
