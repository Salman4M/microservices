#main.py

import os
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from jose import jwt, JWTError
from dotenv import load_dotenv

import redis
import logging

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_LIFETIME_MINUTES = int(os.getenv('ACCESS_TOKEN_LIFETIME_MINUTES', 15))
REFRESH_TOKEN_LIFETIME_DAYS = int(os.getenv('REFRESH_TOKEN_LIFETIME_DAYS', 7))
REDIS_HOST = os.getenv('REDIS_HOST', 'redis_service')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://web:8000')

# Redis client for token blacklisting
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="JWT Authentication Service"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Security
security = HTTPBearer()

# Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class VerifyTokenRequest(BaseModel):
    token: str

class TokenPayload(BaseModel):
    sub: str
    exp: int
    iat: int

# Helper Functions
def add_to_blacklist(token: str):
    """Add token to blacklist in Redis"""
    try:
        redis_client.sadd("blacklisted_tokens", token)
        logger.info(f"Token added to blacklist")
    except Exception as e:
        logger.error(f"Failed to blacklist token: {e}")

def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    try:
        return redis_client.sismember("blacklisted_tokens", token)
    except Exception as e:
        logger.error(f"Failed to check blacklist: {e}")
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
    """Authenticate user via User Service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{USER_SERVICE_URL}/api/user/login/',
                json={'email': email, 'password': password},
                timeout=10.0
            )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Login failed for {email}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"User service communication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable"
        )

# Endpoints
@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "service": "Auth Service",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    """Health check with service dependencies"""
    redis_status = "healthy"
    try:
        redis_client.ping()
    except:
        redis_status = "unhealthy"
    
    return {
        "status": "healthy" if redis_status == "healthy" else "degraded",
        "redis": redis_status
    }

@app.post("/api/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """Login endpoint - authenticates user and returns JWT tokens"""
    user_data = await authenticate_user(credentials.email, credentials.password)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user_uuid = user_data.get('uuid')
    if not user_uuid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User UUID not available"
        )
    
    access_token = create_access_token(user_uuid)
    refresh_token = create_refresh_token(user_uuid)
    
    logger.info(f"User {user_uuid} logged in successfully")
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.post("/api/refresh", response_model=TokenResponse)
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
        
        logger.info(f"Token refreshed for user {user_uuid}")
        
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

@app.post("/api/verify")
def verify(request: VerifyTokenRequest):
    """Verify token validity"""
    try:
        payload = verify_token(request.token)
        return {
            "valid": True,
            "user_uuid": payload.get('sub'),
            "expires_at": payload.get('exp')
        }
    except HTTPException:
        return {"valid": False}

@app.post("/api/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout endpoint - blacklists the access token"""
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        add_to_blacklist(token)
        logger.info(f"User {payload.get('sub')} logged out")
        return {"detail": "Successfully logged out"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@app.post("/api/revoke-refresh")
def revoke_refresh(request: RefreshTokenRequest):
    """Revoke a refresh token"""
    try:
        payload = verify_token(request.refresh_token)
        add_to_blacklist(request.refresh_token)
        logger.info(f"Refresh token revoked for user {payload.get('sub')}")
        return {"detail": "Refresh token revoked"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token revocation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token revocation failed"
        )

# Metrics endpoint for Prometheus
@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    blacklist_size = redis_client.scard("blacklisted_tokens")
    return {
        "blacklisted_tokens": blacklist_size
    }


@app.get("/health")
def health():
    """Health check with service dependencies"""
    redis_status = "healthy"
    try:
        redis_client.ping()
    except Exception as e:  # ← Catch specific exception
        redis_status = "unhealthy"
        logger.error(f"Redis health check failed: {e}")
    
    return {
        "status": "healthy" if redis_status == "healthy" else "degraded",
        "redis": redis_status
    }