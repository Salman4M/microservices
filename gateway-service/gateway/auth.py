import os
import httpx
import re
from datetime import datetime, timedelta, timezone
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from dotenv import load_dotenv
from typing import Set

from .services import SERVICE_URLS
from .logging import logger
from .redis_client import redis_client


load_dotenv()


PUBLIC_PATHS = [
    '/', 
    '/openapi.json', 
    '/docs', 
    '/docs/', 
    '/redoc', 
    '/favicon.ico',
    '/public/',
    '/user/openapi.json',
    '/shop/openapi.json',
    '/product/openapi.json',
]

PUBLIC_ENDPOINTS = {
    # User endpoints
    '/user/api/user/login': ['POST'],
    '/user/api/user/register': ['POST'],
    '/user/api/user/password-reset/request': ['POST'],
    '/user/api/user/password-reset/confirm': ['POST'],

    # Shop endpoints
    '/shop/api/shops/': ['GET'],
    '/shop/api/shops/{shop_slug}/': ['GET'],
    '/shop/api/shops/{shop_uuid}/': ['GET'],
    '/shop/api/branches/{shop_branch_slug}/': ['GET'],
    '/shop/api/comments/{shop_slug}/': ['GET'],
    '/shop/api/media/{shop_slug}/': ['GET'],
    '/shop/api/social-media/{shop_slug}/': ['GET'],

    # Product endpoints
    '/product/': ['GET'],
    '/product/api/categories/': ['GET'],
    '/product/api/categories/{category_id}': ['GET'],
    '/product/api/products/': ['GET'],
    '/product/api/products/{product_id}': ['GET'],
    '/product/api/products/{product_id}/variations/': ['GET'],
    '/product/api/products/{product_id}/variations/{variation_id}': ['GET'],
    '/product/api/products/variations/{variation_id}': ['GET'],
    '/product/api/products/variations/{variation_id}/images/': ['GET'],
    '/product/api/products/variations/{variation_id}/comments/': ['GET'],
}


JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')
HEADER = 'Bearer'
ACCESS_TOKEN_LIFETIME_MINUTES = int(os.getenv('ACCESS_TOKEN_LIFETIME_MINUTES', 60))
REFRESH_TOKEN_LIFETIME_DAYS = int(os.getenv('REFRESH_TOKEN_LIFETIME_DAYS', 7))

BLACKLISTED_TOKENS: Set[str] = set()


def add_to_blacklist(token: str):
    redis_client.sadd("blacklisted_tokens", token)


def is_token_blacklisted(token: str) -> bool:
    return redis_client.sismember("blacklisted_tokens", token)


def is_endpoint_public(path: str, method: str) -> bool:
    """Check if an endpoint is public (doesn't require authentication)"""
    
    # Check exact path matches first
    if any(path == p or path.startswith(p + '/') for p in PUBLIC_PATHS):
        return True
    
    # ✅ NEW: Normalize path - remove trailing slashes for comparison
    normalized_path = path.rstrip('/')
    
    # Check public endpoints with pattern matching
    for public_path, allowed_methods in PUBLIC_ENDPOINTS.items():
        # ✅ NEW: Normalize the public path pattern too
        normalized_pattern = public_path.rstrip('/')
        
        # Replace {param} with regex pattern to match any value
        pattern = re.sub(r'\{[^}]+\}', r'[^/]+', normalized_pattern)
        
        # ✅ NEW: Add anchors for exact matching
        full_pattern = f'^{pattern}$'
        
        # Check if path matches pattern
        if re.match(full_pattern, normalized_path):
            if method.upper() in [m.upper() for m in allowed_methods]:
                # ✅ NEW: Added logging
                logger.info(f"Path {path} matched public pattern {public_path} for method {method}")
                return True
            else:
                # ✅ NEW: Added logging for debugging
                logger.warning(f"Path {path} matched pattern {public_path} but method {method} not allowed")
                return False
    
    # ✅ NEW: Added logging
    logger.info(f"Path {path} is not public, authentication required")
    return False


def create_access_token(payload: dict):
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_LIFETIME_MINUTES)
    payload.update({'exp': expire})
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(payload: dict):
    expire = datetime.now(tz=timezone.utc) + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)
    payload.update({'exp': expire})
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


async def verify_jwt(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer"):
        logger.warning("No Authorization header found or invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not found or incorrect format."
        )
    
    token = auth_header.split(" ")[1]
    if is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked (logged out).")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        request.state.user = payload  
        logger.info(f"JWT verified for user: {payload.get('sub')}")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired."
        )


async def handle_login(request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        res = await client.post(f'{SERVICE_URLS['user']}/api/user/login/', json=body)

    if res.status_code != 200:
        return JSONResponse(res.json(), status_code=res.status_code)

    user = res.json()
    user_uuid = user.get('uuid')
    if not user_uuid:
        return JSONResponse({'detail': 'User UUID not returned'}, status_code=500)

    access = create_access_token({'sub': str(user_uuid)})
    refresh = create_refresh_token({'sub': str(user_uuid)})
    return JSONResponse({
        'access_token': access,
        'refresh_token': refresh,
        'token_type': 'Bearer'
    })


async def handle_logout(request: Request):
    auth_header = request.headers.get("Authorization")
    
    # Parse body safely (optional)
    body = {}
    refresh_token = None
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token")
    except Exception:
        pass  # Body optional
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    access_token = auth_header.split(" ")[1]
    add_to_blacklist(access_token)
    
    if refresh_token:
        add_to_blacklist(refresh_token)
    
    return JSONResponse({
        "detail": "Successfully logged out"
    }, status_code=200)

