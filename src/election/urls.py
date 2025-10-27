from django.urls import path
from .views import ElectionListView, VoteView, ResultsView, VotePageView, ResultsPageView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # API Endpoints
    path('list/', ElectionListView.as_view(), name='election_list'),
    path('vote/', VoteView.as_view(), name='api_vote'),
    path('results/<int:election_id>/', ResultsView.as_view(), name='api_results'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
