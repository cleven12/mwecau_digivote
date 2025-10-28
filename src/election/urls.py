from django.urls import path
from .views import (
    ElectionListView, VoteView, ResultsView,
    VotePageView, ResultsPageView
)
from .views_candidate import (
    CandidateCreateView, CandidateDetailView,
    CandidateListView
)
from .views_voting import (
    ElectionVotingView, PositionCandidatesView
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Election Endpoints
    path('list/', ElectionListView.as_view(), name='election_list'),
    path('vote/', VoteView.as_view(), name='api_vote'),
    path('results/<int:election_id>/', ResultsView.as_view(), name='api_results'),
    
    # Voting Interface Endpoints
    path('voting/<int:election_id>/', ElectionVotingView.as_view(), name='election_voting'),
    path('positions/<int:position_id>/candidates/', PositionCandidatesView.as_view(), name='position_candidates'),
    
    # Candidate Endpoints
    path('candidates/', CandidateListView.as_view(), name='candidate_list'),
    path('candidates/apply/', CandidateCreateView.as_view(), name='candidate_apply'),
    path('candidates/<int:pk>/', CandidateDetailView.as_view(), name='candidate_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
