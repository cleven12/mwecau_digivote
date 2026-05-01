# core/urls.py
from django.urls import path
from .views_ui import (
    home, login_view, logout_view, register_view, dashboard_view, profile_edit_view,
    contributors_view, password_reset_request_view, password_reset_confirm_view,
    password_reset_complete_view,
)
from .views_commissioner import (
    commissioner_dashboard,
    dashboard_stats_api,
    election_analytics_api,
    verify_user_api,
    pending_verifications_api,
    observer_dashboard,
    observer_election_details_api,
    observer_votes_api,
    observer_tokens_api
)

app_name = "core"

urlpatterns = [
    # Home page
    path('', home, name='home'),
    # Contributor page
    path('contributors/', contributors_view, name='contributors'),
    
    # Django session-based authentication
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/edit/', profile_edit_view, name='profile_edit'),
    path('password-reset/', password_reset_request_view, name='password_reset'),
    path('password-reset/confirm/<uidb64>/<token>/', password_reset_confirm_view, name='password_reset_confirm'),
    path('password-reset/complete/', password_reset_complete_view, name='password_reset_complete'),
    
    # Commissioner Dashboard
    path('commissioner/', commissioner_dashboard, name='commissioner_dashboard'),
    path('api/commissioner/stats/', dashboard_stats_api, name='commissioner_stats_api'),
    path('api/commissioner/election/<int:election_id>/analytics/', election_analytics_api, name='election_analytics_api'),
    path('api/commissioner/verify-user/<int:user_id>/', verify_user_api, name='verify_user_api'),
    path('api/commissioner/pending-verifications/', pending_verifications_api, name='pending_verifications_api'),
    
    # Election Observer Dashboard
    path('observer/', observer_dashboard, name='observer_dashboard'),
    path('api/observer/election/<int:election_id>/', observer_election_details_api, name='observer_election_details_api'),
    path('api/observer/votes/', observer_votes_api, name='observer_votes_api'),
    path('api/observer/tokens/', observer_tokens_api, name='observer_tokens_api'),


]