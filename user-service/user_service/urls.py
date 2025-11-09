# user-service/user_service/urls.py
from django.urls import path
from .views import (
    RegisterView, 
    LogoutView, 
    UserProfileView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    validate_credentials,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('internal/validate-credentials/', validate_credentials),  
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]