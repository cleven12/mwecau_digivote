from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.core.cache import cache
from .models import Election, Position, Candidate, Vote
from .tasks import send_vote_confirmation_email
from .serializers import VoteCreateSerializer, PositionResultSerializer, CandidateListSerializer
from core.throttles import VoteSubmitThrottle


class VoteView(APIView):
    """
    Minimal API endpoint for vote submission.
    POST /api/election/{election_id}/submit/
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [VoteSubmitThrottle]

    def post(self, request, election_id):
        serializer = VoteCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            token_obj = serializer.token_obj
            election = serializer.election
            election_level = serializer.election_level
            candidate = serializer.candidate

            vote = Vote.objects.create(
                token=token_obj,
                candidate=candidate,
            )

            token_obj.mark_as_used()
            cache.delete(f'election_results:{election_id}')
            send_vote_confirmation_email.delay(request.user.id, election.id, election_level.id)

            return Response({'message': 'Vote successfully cast.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResultsView(APIView):
    """
    Minimal API endpoint for election results.
    GET /api/election/{election_id}/results/
    """
    permission_classes = [IsAuthenticated] 

    def get(self, request, election_id):
        try:
            election = Election.objects.get(id=election_id)
        except Election.DoesNotExist:
             return Response({'error': 'Election not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not (request.user.is_commissioner() or request.user.is_staff or election.has_ended):
            return Response({'error': 'Results are not available yet.'}, status=status.HTTP_403_FORBIDDEN)

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
                
                total_votes_for_level_position = sum(vote_counts.values())

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

                results_data.append({
                    'position_id': position.id,
                    'position_title': position.title,
                    'total_votes_cast': total_votes_for_level_position,
                    'candidates': candidate_results
                })

        serializer = PositionResultSerializer(results_data, many=True)
        return Response(serializer.data)
