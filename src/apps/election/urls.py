from django.urls import path
from .views import ElectionCreateView, ElectionListView, VoteView, ResultsView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('create/', ElectionCreateView.as_view(), name='election_create'),
    path('list/', ElectionListView.as_view(), name='election_list'),
    path('vote/', VoteView.as_view(), name='vote'),
    path('results/<int:election_id>/', ResultsView.as_view(), name='results'),
]

urlpatterns += static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )