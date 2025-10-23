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

# # election/urls.py
# from django.urls import path
# from django.conf import settings
# from django.conf.urls.static import static
# from django.urls import path
# from . import views

# urlpatterns = [
#     # --- Public/User Views ---
#     path('list/', views.ElectionListView.as_view(), name='election_list'),
#     path('detail/<int:pk>/', views.ElectionDetailView.as_view(), name='election_detail'), # Added detail view
#     path('vote/', views.VoteView.as_view(), name='vote'),
#     path('results/<int:election_id>/', views.ResultsView.as_view(), name='results'),

#     # --- Admin Views ---
#     path('create/', views.ElectionCreateView.as_view(), name='election_create'),
#     path('update/<int:pk>/', views.ElectionDetailView.as_view(), name='election_update'), # PUT/PATCH for update
#     path('delete/<int:pk>/', views.ElectionDetailView.as_view(), name='election_delete'), # DELETE

#     path('position/create/', views.PositionCreateView.as_view(), name='position_create'),
#     path('position/detail/<int:pk>/', views.PositionDetailView.as_view(), name='position_detail'),
#     path('position/update/<int:pk>/', views.PositionDetailView.as_view(), name='position_update'), # PUT/PATCH
#     path('position/delete/<int:pk>/', views.PositionDetailView.as_view(), name='position_delete'), # DELETE

#     path('candidate/create/', views.CandidateCreateView.as_view(), name='candidate_create'),
#     path('candidate/detail/<int:pk>/', views.CandidateDetailView.as_view(), name='candidate_detail'),
#     path('candidate/update/<int:pk>/', views.CandidateDetailView.as_view(), name='candidate_update'), # PUT/PATCH
#     path('candidate/delete/<int:pk>/', views.CandidateDetailView.as_view(), name='candidate_delete'), # DELETE

#     # --- Admin Management/Oversight Views ---
#     path('tokens/', views.VoterTokenListView.as_view(), name='voter_token_list'), 
#     path('token/detail/<int:pk>/', views.VoterTokenDetailView.as_view(), name='voter_token_detail'),

#     path('votes/', views.VoteListView.as_view(), name='vote_list'), # Admin view for listing votes
# ]

# # Serve media files in development
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
