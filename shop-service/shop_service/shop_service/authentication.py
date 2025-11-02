from rest_framework.authentication import BaseAuthentication
import uuid


class GatewayHeaderAuthentication(BaseAuthentication):
    def authenticate(self, request):
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return None
        try:
            uuid.UUID(user_id)
            class ShopUser:
                def __init__(self, user_id):
                    self.id = user_id
                    self.pk = user_id
                    self.is_authenticated = True
                    self.is_anonymous = False
                
                def __str__(self):
                    return f"ShopUser({self.id})"
            
            return (ShopUser(user_id), None)
        
        except (ValueError, TypeError):
            return None