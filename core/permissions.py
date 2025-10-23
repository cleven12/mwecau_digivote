from rest_framework import permissions


class IsVoter(permissions.BasePermission):
    """Permission class to check if user is a voter."""
    
    message = "Only voters can perform this action."
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a voter."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == request.user.ROLE_VOTER
        )


class IsCandidate(permissions.BasePermission):
    """Permission class to check if user is a candidate."""
    
    message = "Only candidates can perform this action."
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a candidate."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == request.user.ROLE_CANDIDATE
        )


class IsClassLeader(permissions.BasePermission):
    """Permission class to check if user is a class leader."""
    
    message = "Only class leaders can perform this action."
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a class leader."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == request.user.ROLE_CLASS_LEADER
        )


class IsCommissioner(permissions.BasePermission):
    """Permission class to check if user is a commissioner."""
    
    message = "Only commissioners can perform this action."
    
    def has_permission(self, request, view):
        """Check if user is authenticated and is a commissioner."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == request.user.ROLE_COMMISSIONER
        )


class IsCommissionerOrReadOnly(permissions.BasePermission):
    """
    Permission class to allow commissioners full access
    and read-only access to others.
    """
    
    message = "Only commissioners can edit this resource."
    
    def has_permission(self, request, view):
        """Check permissions based on request method."""
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == request.user.ROLE_COMMISSIONER
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class to allow owners to edit their own objects,
    and read-only access to others.
    """
    
    message = "You can only edit your own profile."
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the owner of the object."""
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return obj == request.user


class IsVerifiedUser(permissions.BasePermission):
    """Permission class to check if user is verified."""
    
    message = "Only verified users can perform this action."
    
    def has_permission(self, request, view):
        """Check if user is authenticated and verified."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_verified
        )


class CanVoteInElection(permissions.BasePermission):
    """
    Permission class to check if user can vote in a specific election.
    Validates based on state and course restrictions.
    """
    
    message = "You are not eligible to vote in this election."
    
    def has_permission(self, request, view):
        """Basic authentication check."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user is eligible to vote based on position restrictions.
        obj should be a Position or Candidate object.
        """
        from election.models import Position, Candidate
        
        user = request.user
        
        if isinstance(obj, Candidate):
            position = obj.position
        elif isinstance(obj, Position):
            position = obj
        else:
            return False
        
        if position.state and user.state != position.state:
            return False
        
        if position.course and user.course != position.course:
            return False
        
        return True
