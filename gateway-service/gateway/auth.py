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
    '/user/api/user/login/': ['POST'],
    '/user/api/user/register/': ['POST'],
    '/user/api/user/password-reset/request/': ['POST'],
    '/user/api/user/password-reset/confirm/': ['POST'],

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


    # Elasticsearch endpoints
    '/elasticsearch/api/elasticsearch/search/': ['GET'],
    '/elasticsearch/api/elasticsearch/shop/{shop_id}/products/': ['GET']
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
    if any(path == p or path.startswith(p + '/') for p in PUBLIC_PATHS):
        return True
    
    for public_path, allowed_methods in PUBLIC_ENDPOINTS.items():
        pattern = re.sub(r'\{[^}]+\}', '[^/]+', public_path)
        
        if re.match(pattern + '$', path):
            if method.upper() in [m.upper() for m in allowed_methods]:
                return True
            return False
    
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

    try:
        if is_token_blacklisted(token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked (logged out).")
    except Exception as e:
        logger.error(f"Blacklist check failed: {e}")
    
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
    
    


async def get_user_info(user_uuid: str) -> dict:
    """Get user information from user service"""
    try:
        logger.info(f"Fetching user info for user: {user_uuid}")
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f'{SERVICE_URLS['user']}/api/user/profile/',
                headers={'X-User-ID': str(user_uuid)}
            )
        if res.status_code == 200:
            user_info = res.json()
            logger.info(f"User info retrieved successfully for user: {user_uuid}, is_shop_owner: {user_info.get('is_shop_owner')}")
            return user_info
        logger.warning(f"Failed to get user info: status_code={res.status_code}, user={user_uuid}")
        return None
    except Exception as e:
        logger.error(f"Failed to get user info: {e}")
        return None


async def get_shop_uuid_by_user(user_uuid: str) -> str:
    """Get shop UUID from shop service by user UUID"""
    try:
        logger.info(f"Fetching shop UUID for user: {user_uuid}")
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f'{SERVICE_URLS['shop']}/api/user/{user_uuid}/'
            )
        if res.status_code == 200:
            shop_data = res.json()
            shop_uuid = shop_data.get('id')
            logger.info(f"Shop UUID retrieved successfully: {shop_uuid} for user: {user_uuid}")
            return shop_uuid
        logger.warning(f"Failed to get shop UUID: status_code={res.status_code}, user={user_uuid}")
        return None
    except Exception as e:
        logger.error(f"Failed to get shop UUID: {e}")
        return None


async def create_tokens_with_shop(user_uuid: str) -> tuple:
    """Create access and refresh tokens, including shop_uuid if user is shop owner"""
    payload = {'sub': str(user_uuid)}
    
    user_info = await get_user_info(user_uuid)
    if user_info and user_info.get('is_shop_owner'):
        logger.info(f"User {user_uuid} is shop owner, fetching shop UUID")
        shop_uuid = await get_shop_uuid_by_user(user_uuid)
        if shop_uuid:
            payload['shop_uuid'] = str(shop_uuid)
            logger.info(f"Added shop_uuid {shop_uuid} to token for user {user_uuid}")
        else:
            logger.warning(f"User {user_uuid} is shop owner but shop UUID not found")
    else:
        logger.info(f"User {user_uuid} is not shop owner")
    
    access = create_access_token(payload.copy())
    refresh = create_refresh_token(payload.copy())
    logger.info(f"Tokens created successfully for user: {user_uuid}")
    return access, refresh


async def handle_login(request):
    logger.info("Login request received")
    body = await request.json()
    async with httpx.AsyncClient() as client:
        res = await client.post(f'{SERVICE_URLS['user']}/api/user/login/', json=body)

    if res.status_code != 200:
        logger.warning(f"Login failed: status_code={res.status_code}")
        return JSONResponse(res.json(), status_code=res.status_code)

    user = res.json()
    user_uuid = user.get('uuid')
    if not user_uuid:
        logger.error("User UUID not returned from user service")
        return JSONResponse({'detail': 'User UUID not returned'}, status_code=500)

    logger.info(f"Login successful for user: {user_uuid}, creating tokens with shop info")
    access, refresh = await create_tokens_with_shop(user_uuid)
    logger.info(f"Login completed successfully for user: {user_uuid}")
    return JSONResponse({
        'access_token': access,
        'refresh_token': refresh,
        'token_type': 'Bearer'
    })


async def handle_refresh_token(request: Request):
    """Handle refresh token request and create new tokens with shop_uuid if applicable"""
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token")
        
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is required")
        
        if is_token_blacklisted(refresh_token):
            raise HTTPException(status_code=401, detail="Refresh token has been revoked")
        
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_uuid = payload.get('sub')
            
            if not user_uuid:
                raise HTTPException(status_code=400, detail="Invalid refresh token")
            
            add_to_blacklist(refresh_token)
            access, refresh = await create_tokens_with_shop(user_uuid)
            return JSONResponse({
                'access_token': access,
                'refresh_token': refresh,
                'token_type': 'Bearer'
            })
            
        except JWTError as e:
            logger.warning(f"Invalid or expired refresh token: {e}")
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling refresh token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


async def handle_logout(request: Request):
    auth_header = request.headers.get("Authorization")
    
    body = {}
    refresh_token = None
    try:
        body = await request.json()
        refresh_token = body.get("refresh_token")
    except Exception:
        pass
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    access_token = auth_header.split(" ")[1]
    add_to_blacklist(access_token)
    
    if refresh_token:
        add_to_blacklist(refresh_token)
    
    return JSONResponse({
        "detail": "Successfully logged out"
    }, status_code=200)