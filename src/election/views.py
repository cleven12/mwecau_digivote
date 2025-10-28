# election/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Count, Sum
from django.views.generic import TemplateView
from django.core.exceptions import ValidationError
from .models import Election, ElectionLevel, Position, Candidate, VoterToken, Vote
from core.models import User
from .tasks import send_vote_confirmation_email
from .serializers import (
    ElectionListSerializer, 
    PositionDetailSerializer, 
    CandidateListSerializer, 
    VoterTokenSerializer, 
    VoteCreateSerializer,
    PositionResultSerializer
)

# --- Election Views ---
class ElectionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # active or upcoming elections to regular users
        elections = Election.objects.filter(is_active=True)
        serializer = ElectionListSerializer(elections, many=True, context={'request': request})
        return Response(serializer.data)

class ElectionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            election = Election.objects.get(pk=pk)
            serializer = ElectionListSerializer(election, context={'request': request})
            return Response(serializer.data)
        except Election.DoesNotExist:
            return Response({'error': 'Election not found.'}, status=status.HTTP_404_NOT_FOUND)
            
    def patch(self, request, pk):
        """Update election status (activate/deactivate)."""
        if not request.user.can_manage_elections():
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            election = Election.objects.get(pk=pk)
            action = request.data.get('action')
            
            if action == 'activate':
                try:
                    success = election.activate()
                    if success:
                        return Response({'message': 'Election activated and notifications sent.'})
                    return Response({'message': 'Election was already active.'})
                except ValidationError as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                    
            elif action == 'deactivate':
                success = election.deactivate()
                if success:
                    return Response({'message': 'Election deactivated.'})
                return Response({'message': 'Election was already inactive.'})
                
            return Response({'error': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)
            
        except Election.DoesNotExist:
            return Response({'error': 'Election not found.'}, status=status.HTTP_404_NOT_FOUND)


class ElectionCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not request.user.can_manage_elections():
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = ElectionListSerializer(data=request.data)
        if serializer.is_valid():
            # Save with is_active=False initially
            election = serializer.save(is_active=False)
            
            # If auto_activate is requested and start date is now/past
            if request.data.get('auto_activate'):
                try:
                    if timezone.now() >= election.start_date:
                        election.activate()
                except ValidationError as e:
                    return Response({
                        'warning': f'Election created but activation failed: {str(e)}'
                    }, status=status.HTTP_201_CREATED)
                    
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- Voting Views ---
class VoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VoteCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            token_obj = serializer.token_obj
            election = serializer.election
            election_level = serializer.election_level
            candidate = serializer.candidate

            # --- Create the Vote ---
            # Vote model's save method handles denormalization
            vote = Vote.objects.create(
                token=token_obj,
                candidate=candidate,
            )

            # --- Mark Token as Used ---
            token_obj.mark_as_used()

            # --- Trigger Confirmation Email ---
            send_vote_confirmation_email(request.user.id, election.id, election_level.id) 

            return Response({'message': 'Vote successfully cast.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Results Views ---
class ResultsView(APIView):
    # If IsAuthenticated , or if should be public after election
    permission_classes = [IsAuthenticated] 

    def get(self, request, election_id):
        try:
            election = Election.objects.get(id=election_id)
        except Election.DoesNotExist:
             return Response({'error': 'Election not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user can see results (e.g., is admin, is commissioner, election ended)
        if not (request.user.is_commissioner() or request.user.is_staff or election.has_ended):
            return Response({'error': 'Results are not available yet.'}, status=status.HTTP_403_FORBIDDEN)

        # --- Aggregate Results ---
        results_data = []
        election_levels = election.levels.all()

        for level in election_levels:
            positions = Position.objects.filter(election_level=level)

            for position in positions:
                candidate_votes = Vote.objects.filter(
                    election=election, 
                    election_level=level, 
                    candidate__position=position
                ).values('candidate').annotate(vote_count=Count('candidate'))

                vote_counts = {item['candidate']: item['vote_count'] for item in candidate_votes}
                
                # Total votes cast for position/level
                total_votes_for_level_position = sum(vote_counts.values())

                # Get candidate details
                candidates_for_position = Candidate.objects.filter(position=position)
                candidate_results = []
                for candidate in candidates_for_position:
                    count = vote_counts.get(candidate.id, 0)
                    percentage = (count / total_votes_for_level_position * 100) if total_votes_for_level_position > 0 else 0
                    candidate_results.append({
                        'candidate_id': candidate.id,
                        'candidate_name': candidate.user.get_full_name(),
                        'candidate_image_url': CandidateListSerializer().get_image_url(candidate),
                         'vote_count': count,
                         'vote_percentage': round(percentage, 2)
                    })

                # Append results for this position
                results_data.append({
                    'position_id': position.id,
                    'position_title': position.title,
                    'total_votes_cast': total_votes_for_level_position,
                    'candidates': candidate_results
                })

        serializer = PositionResultSerializer(results_data, many=True)
        return Response(serializer.data)
            # OR
        # return Response(results_data) #raw aggregated data for now


# --- Template Views for Frontend UI ---
class VotePageView(TemplateView):
    """Voting page view."""
    template_name = 'election/vote_api.html'

class ResultsPageView(TemplateView):
    """Results page view."""
    template_name = 'election/results_api.html'