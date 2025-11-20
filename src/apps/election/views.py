# election/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Count, Sum
from .models import Election, ElectionLevel, Position, Candidate, VoterToken, Vote
from .serializers import (
    ElectionListSerializer, 
    PositionDetailSerializer, 
    CandidateListSerializer, 
    VoterTokenSerializer, 
    VoteCreateSerializer,
    PositionResultSerializer #  results serializer
)
from core.models import User
# Import the Celery task
# from .tasks import send_voter_token_email
from .tasks import send_vote_confirmation_email
# --- Election Views ---
class ElectionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Show only active or upcoming elections to regular users
        # Admins might see all with a filter?
        elections = Election.objects.filter(is_active=True) # Or adjust queryset logic
        serializer = ElectionListSerializer(elections, many=True, context={'request': request})
        return Response(serializer.data)

# Placeholder for ElectionDetailView if needed
# class ElectionDetailView(...) ...

# --- Voting Views ---
class VoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VoteCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Get validated data and objects from serializer
            token_obj = serializer.token_obj
            election = serializer.election
            election_level = serializer.election_level
            candidate = serializer.candidate

            # --- Create the Vote ---
            # The Vote model's save method handles denormalization
            vote = Vote.objects.create(
                token=token_obj,
                candidate=candidate,
                # election and election_level are set by Vote.save()
            )

            # --- Mark Token as Used ---
            token_obj.mark_as_used() # This updates used_at as well

            # --- Trigger Confirmation Email (Celery) ---
            # send_vote_confirmation_email.delay(request.user.id, election.id, election_level.id)
            # Or, if the task uses token ID:
            # send_vote_confirmation_email.delay(token_obj.id) 

            return Response({'message': 'Vote successfully cast.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Results Views ---
class ResultsView(APIView):
    # Consider if IsAuthenticated is enough, or if results should be public after election ends
    permission_classes = [IsAuthenticated] 

    def get(self, request, election_id):
        try:
            election = Election.objects.get(id=election_id)
        except Election.DoesNotExist:
             return Response({'error': 'Election not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Optional: Check if user can see results (e.g., is admin, is commissioner, election ended)
        # if not (request.user.is_commissioner() or request.user.is_staff or election.has_ended):
        #     return Response({'error': 'Results are not available yet.'}, status=status.HTTP_403_FORBIDDEN)

        # --- Aggregate Results ---
        results_data = []
        # Get all positions.levels for this election
        election_levels = election.levels.all()

        for level in election_levels:
            # Get all positions for this level in this election
            positions = Position.objects.filter(election_level=level)

            for position in positions:
                # Count votes for each candidate in this specific position
                candidate_votes = Vote.objects.filter(
                    election=election, 
                    election_level=level, 
                    candidate__position=position
                ).values('candidate').annotate(vote_count=Count('candidate'))

                # Create a map of candidate_id -> vote_count for easy lookup
                vote_counts = {item['candidate']: item['vote_count'] for item in candidate_votes}
                
                # Total votes cast for this position/level
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
                        # Add image URL if needed, requires request context
                        # 'candidate_image_url': CandidateListSerializer().get_image_url(candidate), # Needs request context
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

        # You could serialize results_data with PositionResultSerializer if needed
        # serializer = PositionResultSerializer(results_data, many=True)
        # return Response(serializer.data)
        
        return Response(results_data) # Return raw aggregated data for now

# --- Admin Views ---
class ElectionCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        # Use ElectionListSerializer or a dedicated create serializer if fields differ
        serializer = ElectionListSerializer(data=request.data)
        if serializer.is_valid():
            # Save the election
            election = serializer.save()
            
            # --- Post-Creation Logic: Generate Tokens ---
            # Important: M2M relationships (like levels) are usually set *after* the main object is saved.
            # Ensure levels are associated before generating tokens.
            # The request data should include level IDs.
            level_ids = request.data.get('levels', []) # Expect a list of level IDs
            if level_ids:
                 levels = ElectionLevel.objects.filter(id__in=level_ids)
                 election.levels.set(levels) # Associate levels

            # Trigger token generation for all verified users
            # This should ideally be queued as a Celery task for large user bases
            verified_users = User.objects.filter(is_verified=True)
            for user in verified_users:
                # Call the method on the manager
                # Note: The method signature in models.py proposal was `generate_voter_tokens(self, user_id, election_id)`
                # But your initial UserManager code used `generate_voter_token(self, user_id, election_id)`
                # Assuming the updated manager method is `generate_voter_tokens_for_election`
                try:
                     User.objects.generate_voter_tokens_for_election(user.id, election.id)
                     # Queue email task
                     send_vote_confirmation_email.delay(user.id, election.id)
                except Exception as e:
                     # Log error, maybe add to failed user list in response
                     print(f"Failed to generate tokens for user {user.id}: {e}")

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Placeholder for other admin views like updating elections, managing candidates etc.
# class CandidateCreateView(APIView): ...
# class PositionCreateView(APIView): ...
