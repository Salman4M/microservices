# user_service/authentication.py
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import get_user_model

User = get_user_model()


class GatewayHeaderAuthentication(BaseAuthentication):
    def authenticate(self, request):
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return None  
        try:
            user = User.objects.get(pk=user_id) 
            return (user, None)
        except User.DoesNotExist:
            return None