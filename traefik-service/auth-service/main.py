import os
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, status, Depends, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from dotenv import load_dotenv
import redis
from redis.connection import ConnectionPool
import logging
import asyncio

load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_LIFETIME_MINUTES = int(os.getenv('ACCESS_TOKEN_LIFETIME_MINUTES', 60))
REFRESH_TOKEN_LIFETIME_DAYS = int(os.getenv('REFRESH_TOKEN_LIFETIME_DAYS', 7))
REDIS_HOST = os.getenv('REDIS_HOST', 'redis_service')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://web:8000')

# Redis connection pool with better error handling
redis_pool = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    max_connections=50,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    decode_responses=True
)
redis_client = redis.Redis(connection_pool=redis_pool)

# Initialize FastAPI with OpenAPI configuration
app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="JWT Authentication Service for Microservices",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

security = HTTPBearer()

# Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "YourPassword123"
            }
        }


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class VerifyTokenRequest(BaseModel):
    token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


# Helper Functions
async def add_to_blacklist(token: str) -> bool:
    """Add token to blacklist in Redis with retry"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            redis_client.sadd("blacklisted_tokens", token)
            logger.info(f"Token blacklisted successfully (attempt {attempt + 1})")
            return True
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return False
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    return False


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted with retry"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = redis_client.sismember("blacklisted_tokens", token)
            return bool(result)
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error checking blacklist (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.warning("Redis unavailable - allowing request through")
                return False
        except Exception as e:
            logger.error(f"Error checking blacklist: {e}")
            return False
    return False


def create_access_token(user_uuid: str) -> str:
    """Create JWT access token"""
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES)
    payload = {
        'sub': str(user_uuid),
        'exp': expire,
        'iat': datetime.now(tz=timezone.utc),
        'type': 'access'
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_uuid: str) -> str:
    """Create JWT refresh token"""
    expire = datetime.now(tz=timezone.utc) + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)
    payload = {
        'sub': str(user_uuid),
        'exp': expire,
        'iat': datetime.now(tz=timezone.utc),
        'type': 'refresh'
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    """Authenticate user via User Service internal endpoint with improved retry logic"""
    max_retries = 5  # Increased from 3
    base_delay = 0.5  # Start with shorter delay
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔐 Authentication attempt {attempt + 1}/{max_retries} for: {email}")
            
            # Use longer timeout for first request (DB might be cold)
            timeout_seconds = 10.0 if attempt == 0 else 5.0
            
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    f'{USER_SERVICE_URL}/api/internal/validate-credentials/',
                    json={'email': email, 'password': password},
                    headers={'Content-Type': 'application/json'}
                )
            
            logger.info(f"📬 User service response: {response.status_code}")
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"✅ Authentication successful for: {email}")
                return user_data
            elif response.status_code == 401:
                logger.warning(f"❌ Invalid credentials for: {email}")
                return None
            elif response.status_code == 400:
                logger.warning(f"⚠️ Bad request for: {email}")
                return None
            else:
                logger.error(f"❌ Unexpected status {response.status_code}: {response.text}")
                # Retry on server errors
                if attempt < max_retries - 1 and response.status_code >= 500:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"⏳ Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                return None
                
        except httpx.ConnectError as e:
            logger.error(f"🔌 Connection error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"⏳ Retrying in {delay}s...")
                await asyncio.sleep(delay)
                continue
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User service is unavailable. Please try again."
            )
        except httpx.TimeoutException as e:
            logger.error(f"⏱️ Timeout (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.info(f"⏳ Retrying in {delay}s...")
                await asyncio.sleep(delay)
                continue
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="User service timeout. Please try again."
            )
        except Exception as e:
            logger.error(f"💥 Unexpected error: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service error"
            )
    
    return None


# API Endpoints
@app.get("/", tags=["Health"])
def root():
    """Root endpoint"""
    return {
        "service": "Auth Service",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "login": "/api/login",
            "logout": "/api/logout",
            "refresh": "/api/refresh",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint"""
    redis_status = "healthy"
    
    try:
        redis_client.ping()
    except Exception as e:
        redis_status = "unhealthy"
        logger.error(f"Redis health check failed: {e}")
    
    overall_status = "healthy" if redis_status == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "services": {
            "redis": redis_status,
            "user_service": "unknown"
        },
        "timestamp": datetime.now(tz=timezone.utc).isoformat()
    }


@app.post("/api/login", response_model=TokenResponse, tags=["Authentication"])
async def login(credentials: LoginRequest):
    """
    Login endpoint - authenticates user and returns JWT tokens
    
    - **email**: User email address
    - **password**: User password
    """
    logger.info(f"🔑 Login attempt for: {credentials.email}")
    
    user_data = await authenticate_user(credentials.email, credentials.password)
    
    if not user_data:
        logger.warning(f"🚫 Login failed for: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user_uuid = user_data.get('uuid')
    if not user_uuid:
        logger.error("UUID missing in user data")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User UUID not available"
        )
    
    access_token = create_access_token(user_uuid)
    refresh_token = create_refresh_token(user_uuid)
    
    logger.info(f"✅ User {user_uuid} logged in successfully")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@app.post("/api/refresh", response_model=TokenResponse, tags=["Authentication"])
def refresh(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    try:
        payload = verify_token(request.refresh_token)
        
        if payload.get('type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_uuid = payload.get('sub')
        access_token = create_access_token(user_uuid)
        
        logger.info(f"🔄 Token refreshed for user {user_uuid}")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=request.refresh_token
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@app.post("/api/verify", tags=["Authentication"])
def verify(request: VerifyTokenRequest):
    """Verify token validity (for internal use)"""
    try:
        payload = verify_token(request.token)
        return {
            "valid": True,
            "user_uuid": payload.get('sub'),
            "expires_at": payload.get('exp')
        }
    except HTTPException:
        return {"valid": False}


@app.get("/api/verify-forward", tags=["Authentication"], include_in_schema=False)
@app.post("/api/verify-forward", tags=["Authentication"], include_in_schema=False)
async def verify_forward(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """ForwardAuth endpoint for Traefik middleware"""
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_uuid = payload.get('sub')
        
        response = Response(status_code=200)
        response.headers["X-User-ID"] = str(user_uuid)
        logger.debug(f"✓ Verified token for user: {user_uuid}")
        return response
        
    except HTTPException as e:
        logger.warning(f"Token verification failed: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )


@app.post("/api/logout", tags=["Authentication"])
async def logout(  # 👈 NOW async!
    logout_req: Optional[LogoutRequest] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Logout endpoint - blacklists the access token
    
    Optionally provide refresh_token in request body to blacklist it too
    """
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        success = await add_to_blacklist(token)  # 👈 NOW awaited!
        
        if not success:
            logger.error("Failed to blacklist token - Redis unavailable")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Logout failed - service unavailable"
            )
        
        # Blacklist refresh token if provided
        if logout_req and logout_req.refresh_token:
            await add_to_blacklist(logout_req.refresh_token)  # 👈 NOW awaited!
        
        logger.info(f"👋 User {payload.get('sub')} logged out")
        return {"detail": "Successfully logged out"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@app.post("/api/revoke-refresh", tags=["Authentication"])
async def revoke_refresh(request: RefreshTokenRequest):  # 👈 NOW async!
    """Revoke a refresh token"""
    try:
        payload = verify_token(request.refresh_token)
        success = await add_to_blacklist(request.refresh_token)  # 👈 NOW awaited!
        
        if not success:
            logger.error("Failed to revoke token - Redis unavailable")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Token revocation failed - service unavailable"
            )
        
        logger.info(f"🚫 Refresh token revoked for user {payload.get('sub')}")
        return {"detail": "Refresh token revoked"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token revocation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token revocation failed"
        )

        
@app.get("/metrics", tags=["Monitoring"], include_in_schema=False)
def metrics():
    """Prometheus metrics endpoint"""
    try:
        blacklist_size = redis_client.scard("blacklisted_tokens")
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        blacklist_size = -1
    
    return {
        "blacklisted_tokens": blacklist_size,
        "service": "auth-service"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info("🚀 Auth Service starting up...")
    
    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
    
    # Test User Service connection
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f'{USER_SERVICE_URL}/api/health/', timeout=5.0)
            if response.status_code == 200:
                logger.info("✅ User Service connection successful")
            else:
                logger.warning(f"⚠️ User Service returned {response.status_code}")
    except Exception as e:
        logger.warning(f"⚠️ Could not connect to User Service: {e}")
    
    logger.info("✅ Auth Service ready!")