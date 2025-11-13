from fastapi import FastAPI, HTTPException, status, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import redis

app = FastAPI(title="Authentication Service", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-this')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_LIFETIME_MINUTES = int(os.getenv('ACCESS_TOKEN_LIFETIME_MINUTES', 60))
REFRESH_TOKEN_LIFETIME_DAYS = int(os.getenv('REFRESH_TOKEN_LIFETIME_DAYS', 7))
USER_SERVICE_URL = os.getenv('USER_SERVICE', 'http://user-service:8000')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis_service')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Redis client for token blacklist
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

# Models
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"

class TokenValidationRequest(BaseModel):
    token: str

class TokenValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    message: Optional[str] = None

# Helper functions
def create_access_token(payload: dict):
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES)
    payload.update({'exp': expire, 'type': 'access'})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(payload: dict):
    expire = datetime.now(tz=timezone.utc) + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)
    payload.update({'exp': expire, 'type': 'refresh'})
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def is_token_blacklisted(token: str) -> bool:
    try:
        return redis_client.sismember("blacklisted_tokens", token)
    except Exception as e:
        print(f"Redis error: {e}")
        return False

def blacklist_token(token: str):
    try:
        redis_client.sadd("blacklisted_tokens", token)
    except Exception as e:
        print(f"Redis error: {e}")

# Endpoints
@app.get("/")
def root():
    return {"service": "Authentication Service", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """Login and get JWT tokens"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{USER_SERVICE_URL}/api/user/login/',
                json={"email": credentials.email, "password": credentials.password}
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        user_data = response.json()
        user_uuid = user_data.get('uuid')
        
        if not user_uuid:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User UUID not returned"
            )
        
        # Create tokens
        access_token = create_access_token({'sub': str(user_uuid)})
        refresh_token = create_refresh_token({'sub': str(user_uuid)})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"User service unavailable: {str(e)}"
        )

@app.post("/api/auth/validate", response_model=TokenValidationResponse)
async def validate_token(request: TokenValidationRequest):
    """Validate JWT token - used by Nginx auth_request"""
    token = request.token
    
    # Check blacklist
    if is_token_blacklisted(token):
        return TokenValidationResponse(
            valid=False,
            message="Token has been revoked"
        )
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('sub')
        
        if not user_id:
            return TokenValidationResponse(
                valid=False,
                message="Invalid token payload"
            )
        
        return TokenValidationResponse(
            valid=True,
            user_id=user_id
        )
    
    except JWTError as e:
        return TokenValidationResponse(
            valid=False,
            message=f"Token validation failed: {str(e)}"
        )

@app.post("/api/auth/logout")
async def logout(authorization: str = Header(None)):
    """Logout and blacklist token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    blacklist_token(token)
    
    return {"message": "Successfully logged out"}

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(authorization: str = Header(None)):
    """Refresh access token using refresh token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        if payload.get('type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get('sub')
        
        # Create new tokens
        access_token = create_access_token({'sub': user_id})
        refresh_token = create_refresh_token({'sub': user_id})
        
        # Blacklist old refresh token
        blacklist_token(token)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )