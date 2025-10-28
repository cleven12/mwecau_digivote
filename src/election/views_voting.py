from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Prefetch
from .models import Election, Position, Candidate, VoterToken
from .serializers_voting import ElectionVotingSerializer, ElectionPositionSerializer


class ElectionVotingView(APIView):
    """
    View for retrieving election details with positions and candidates for voting.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, election_id):
        """
        Get election details with all positions and their candidates.
        Also includes voting eligibility and status for the requesting user.
        """
        try:
            election = get_object_or_404(Election, pk=election_id)
            
            if not election.is_active:
                return Response({
                    'status': 'error',
                    'message': 'This election is not currently active.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ElectionVotingSerializer(
                election,
                context={'request': request}
            )
            
            return Response({
                'status': 'success',
                'data': serializer.data
            })
            
        except Election.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Election not found.'
            }, status=status.HTTP_404_NOT_FOUND)


class PositionCandidatesView(APIView):
    """
    View for retrieving candidates for a specific position.
    Useful for the voting interface where users select from candidates.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, position_id):
        """Get candidates for a specific position with voting status."""
        try:
            # Get position with its election level and candidates
            position = get_object_or_404(
                Position.objects.select_related('election_level'),
                pk=position_id
            )
            
            # Get the election for this position
            election = position.election_level.elections.first()
            if not election or not election.is_active:
                return Response({
                    'status': 'error',
                    'message': 'This position is not part of an active election.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user has already voted for this position
            has_voted = VoterToken.objects.filter(
                user=request.user,
                election=election,
                election_level=position.election_level,
                is_used=True
            ).exists()
            
            if has_voted:
                return Response({
                    'status': 'error',
                    'message': 'You have already voted for this position.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user has an unused token for this level
            has_token = VoterToken.objects.filter(
                user=request.user,
                election=election,
                election_level=position.election_level,
                is_used=False
            ).exists()
            
            if not has_token:
                return Response({
                    'status': 'error',
                    'message': 'You are not eligible to vote for this position.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get candidates with vote counts
            serializer = ElectionPositionSerializer(
                position,
                context={'request': request}
            )
            
            return Response({
                'status': 'success',
                'data': serializer.data
            })
            
        except Position.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Position not found.'
            }, status=status.HTTP_404_NOT_FOUND)