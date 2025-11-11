from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.db import connection
from Core.authentication import TraefikHeaderAuthentication
from Core.messaging import publisher
from rest_framework.permissions import AllowAny
from datetime import datetime, timezone
import logging
from .serializers import (
    UserSerializer, 
    RegisterSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer
)

logger = logging.getLogger(__name__)

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


#  Health Check Endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify service is running and database is accessible
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "user-service",
        "checks": {}
    }
    
    # Check database connection
    try:
        connection.ensure_connection()
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check if we can query users table
    try:
        User.objects.count()
        health_status["checks"]["user_table"] = "accessible"
    except Exception as e:
        logger.error(f"User table check failed: {e}")
        health_status["checks"]["user_table"] = "inaccessible"
        health_status["status"] = "degraded"
    
    return Response(health_status, status=200 if health_status["status"] == "healthy" else 503)


#  Register 
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        logger.info(f"📝 Registration request for: {request.data.get('email')}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Publish user created event
        if user.is_active:
            try:
                publisher.publish_user_created(
                    user_uuid=str(user.id),
                    email=user.email,
                    is_active=user.is_active
                )
                logger.info(f"✅ User created event published for: {user.email}")
            except Exception as e:
                logger.error(f"❌ Failed to publish user created event: {e}")
        
        logger.info(f"✅ User registered successfully: {user.email}")
        
        return Response({
            "uuid": str(user.id),
            "email": user.email,
            "user": UserSerializer(user, context=self.get_serializer_context()).data
        }, status=status.HTTP_201_CREATED)


#  Internal Credential Validation (called by Auth Service)
@api_view(['POST'])
@permission_classes([AllowAny])
def validate_credentials(request):
    """
    Internal endpoint for credential validation
    This endpoint is called by the Auth Service to validate user credentials
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    logger.info(f"🔐 Credential validation request for: {email}")
    
    if not email or not password:
        logger.warning("⚠️ Missing email or password in request")
        return Response(
            {'error': 'Email and password required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Check database connection first
        connection.ensure_connection()
        
        # Get user from database
        user = User.objects.get(email=email)
        logger.info(f"✓ User found in database: {email}")
        
        # Verify password
        if not user.check_password(password):
            logger.warning(f"❌ Invalid password for: {email}")
            return Response(
                {'error': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"⚠️ Inactive user attempted login: {email}")
            return Response(
                {'error': 'User account is disabled'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        logger.info(f"✅ Credentials valid for: {email} (UUID: {user.id})")
        
        return Response({
            'uuid': str(user.id),
            'email': user.email,
            'is_active': user.is_active,
            'is_shop_owner': user.is_shop_owner
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        logger.warning(f"❌ User not found: {email}")
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        logger.error(f"💥 Database error during validation: {e}", exc_info=True)
        return Response(
            {'error': 'Authentication service error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


#  Logout 
class LogoutView(APIView):
    authentication_classes = [TraefikHeaderAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        logger.info(f"👋 Logout request from user: {request.user.id}")
        return Response(
            {"detail": "Logged out successfully"}, 
            status=status.HTTP_205_RESET_CONTENT
        )


# User Profile
class UserProfileView(APIView):
    authentication_classes = [TraefikHeaderAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request): 
        serializer = UserSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"✓ Profile updated for user: {request.user.id}")
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"✓ Profile partially updated for user: {request.user.id}")
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


# Password Reset Request
class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if user exists
            return Response({"detail": "If an account exists, a reset link has been sent."})

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        frontend_base = getattr(settings, "FRONTEND_PASSWORD_RESET_URL", "http://127.0.0.1:3000/reset-password")
        reset_link = f"{frontend_base}?uid={uid}&token={token}"

        subject = "Password Reset Request"
        message = f"""
Hello {user.first_name or 'User'},

Click this link to reset your password:
👉 {reset_link}

Best regards,
Your Team
        """

        from_email = settings.EMAIL_HOST_USER
        send_mail(subject, message.strip(), from_email, [user.email], fail_silently=False)

        logger.info(f"📧 Password reset email sent to: {email}")
        return Response(
            {"detail": "If an account exists, a reset link has been sent."}, 
            status=status.HTTP_200_OK
        )


# Password Reset Confirm
class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save()

        logger.info(f"🔒 Password reset successfully for user: {user.id}")
        return Response(
            {"detail": "Password has been reset successfully."}, 
            status=status.HTTP_200_OK
        )