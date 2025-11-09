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
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/internal/validate-credentials/', validate_credentials),  
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/profile/', UserProfileView.as_view(), name='user-profile'),
    path('api/password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('api/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]