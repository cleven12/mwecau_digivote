# core/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
# Import your views
from . import views

urlpatterns = [
    # API Endpoints
    path('api/auth/login/', views.UserLoginView.as_view(), name='api_login'),
    path('api/auth/logout/', views.UserLogoutView.as_view(), name='api_logout'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/register/', views.UserRegisterView.as_view(), name='api_register'),
    path('api/auth/complete-registration/', views.CompleteRegistrationView.as_view(), name='api_complete_registration'),
    path('api/auth/verify/request/', views.VerificationRequestView.as_view(), name='api_verification_request'),
    path('api/auth/verify/', views.VerifyUserView.as_view(), name='api_verify_user'),
    path('api/auth/verify/status/', views.VerificationStatusView.as_view(), name='api_verification_status'),
    path('api/auth/forgot-password/', views.ForgotPasswordView.as_view(), name='api_forgot_password'),
    path('api/auth/dashboard/', views.UserDashboardView.as_view(), name='api_dashboard'),
    path('api/auth/contact-commissioner/', views.ContactCommissionerView.as_view(), name='api_contact_commissioner'),
    
    # Reference data endpoints for dropdowns
    path('api/states/', views.StateListView.as_view(), name='api_states'),
    path('api/courses/', views.CourseListView.as_view(), name='api_courses'),
]