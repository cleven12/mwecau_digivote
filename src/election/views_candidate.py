from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import Candidate, Position, Election
from .serializers_candidate import CandidateCreateSerializer, CandidateDetailSerializer


class CandidateCreateView(APIView):
    """Handle candidate applications for election positions."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # For handling image uploads

    def post(self, request):
        """Submit a new candidate application."""
        serializer = CandidateCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                candidate = serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'Application submitted successfully.',
                    'data': CandidateDetailSerializer(
                        candidate,
                        context={'request': request}
                    ).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CandidateDetailView(APIView):
    """Handle retrieving and updating candidate profiles."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_candidate(self, pk, user):
        """Get candidate and check permissions."""
        candidate = get_object_or_404(Candidate, pk=pk)
        
        # Check if user can view this candidate
        if not (user.is_staff or user.is_commissioner() or 
                candidate.user == user or candidate.election.is_active):
            raise PermissionError("You don't have permission to view this candidate.")
        
        return candidate

    def get(self, request, pk):
        """Get candidate details."""
        try:
            candidate = self.get_candidate(pk, request.user)
            serializer = CandidateDetailSerializer(
                candidate,
                context={'request': request}
            )
            return Response(serializer.data)
        except PermissionError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Candidate.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Candidate not found.'
            }, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        """Update candidate bio, platform, or image."""
        try:
            candidate = self.get_candidate(pk, request.user)
            
            # Only allow updates if it's your profile or you're staff/commissioner
            if not (request.user.is_staff or request.user.is_commissioner() or 
                   candidate.user == request.user):
                return Response({
                    'status': 'error',
                    'message': "You don't have permission to edit this profile."
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Only allow updating bio, platform, and image
            allowed_fields = {'bio', 'platform', 'image'}
            update_data = {
                k: v for k, v in request.data.items()
                if k in allowed_fields
            }
            
            serializer = CandidateDetailSerializer(
                candidate,
                data=update_data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'Profile updated successfully.',
                    'data': serializer.data
                })
            
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except PermissionError as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
        except Candidate.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Candidate not found.'
            }, status=status.HTTP_404_NOT_FOUND)


class CandidateListView(APIView):
    """List candidates with various filters."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get candidates list. Supports filtering by:
        - election_id: Get candidates for a specific election
        - position_id: Get candidates for a specific position
        - level_id: Get candidates for a specific election level
        - search: Search by name or registration number
        """
        # Start with all candidates
        queryset = Candidate.objects.select_related(
            'user', 'election', 'position', 'position__election_level'
        ).order_by('position', 'user__first_name')
        
        # Apply filters
        election_id = request.query_params.get('election_id')
        if election_id:
            queryset = queryset.filter(election_id=election_id)
        
        position_id = request.query_params.get('position_id')
        if position_id:
            queryset = queryset.filter(position_id=position_id)
        
        level_id = request.query_params.get('level_id')
        if level_id:
            queryset = queryset.filter(position__election_level_id=level_id)
        
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__registration_number__icontains=search)
            )
        
        # Only show candidates from active elections or if user has permission
        if not (request.user.is_staff or request.user.is_commissioner()):
            queryset = queryset.filter(
                Q(election__is_active=True) |
                Q(user=request.user)  # Always show user's own candidacies
            )
        
        serializer = CandidateDetailSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        })