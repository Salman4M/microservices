from rest_framework.authentication import BaseAuthentication
import uuid
from rest_framework.authentication import BaseAuthentication
import uuid
import logging

logger = logging.getLogger(__name__)


class TraefikHeaderAuthentication(BaseAuthentication):
    """
    Authentication class that extracts user ID from X-User-ID header
    injected by Traefik's ForwardAuth middleware.
    """
    
    def authenticate(self, request):
        # Get X-User-ID header added by Traefik after Auth Service verification
        user_id = request.headers.get("X-User-ID")
        
        if not user_id:
            logger.warning("No X-User-ID header found in request")
            return None
        
        try:
            # Validate UUID format
            uuid.UUID(user_id)
            
            # Create a simple user object
            class OrderUser:
                def __init__(self, user_id):
                    self.id = user_id
                    self.pk = user_id
                    self.is_authenticated = True
                    self.is_anonymous = False
                
                def __str__(self):
                    return f"ShopUser({self.id})"
            
            logger.info(f"Authenticated user: {user_id}")
            return (OrderUser(user_id), None)
        
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user ID format: {user_id}, error: {e}")
            return None



# class GatewayHeaderAuthentication(BaseAuthentication):
#     def authenticate(self, request):
#         user_id = request.headers.get("X-User-ID")
#         if not user_id:
#             return None
#         try:
#             uuid.UUID(user_id)
#             class OrderUser:
#                 def __init__(self, user_id):
#                     self.id = user_id
#                     self.pk = user_id
#                     self.is_authenticated = True
#                     self.is_anonymous = False
                
#                 def __str__(self):
#                     return f"OrderUser({self.id})"
            
#             return (OrderUser(user_id), None)
        
#         except (ValueError, TypeError):
#             return None