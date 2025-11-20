# core/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # API Endpoints
    path('api/login/', views.UserLoginView.as_view(), name='api_login'),
    path('api/logout/', views.UserLogoutView.as_view(), name='api_logout'),
    path('api/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/register/', views.UserRegisterView.as_view(), name='api_register'),
    path('api/complete-registration/', views.CompleteRegistrationView.as_view(), name='api_complete_registration'),
    path('api/verify/request/', views.VerificationRequestView.as_view(), name='api_verification_request'),
    path('api/verify/', views.VerifyUserView.as_view(), name='api_verify_user'),
    path('api/verify/status/', views.VerificationStatusView.as_view(), name='api_verification_status'),
    path('api/forgot-password/', views.ForgotPasswordView.as_view(), name='api_forgot_password'),
    path('api/dashboard/', views.UserDashboardView.as_view(), name='api_dashboard'),
    path('api/contact-commissioner/', views.ContactCommissionerView.as_view(), name='api_contact_commissioner'),
]
