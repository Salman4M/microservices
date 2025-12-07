import httpx
import json
from fastapi import Request
from fastapi.responses import JSONResponse
from .logging import logger
from .auth import verify_jwt, is_endpoint_public, handle_login, handle_logout,handle_refresh_token
from .services import SERVICE_URLS


async def log_requests_middleware(request: Request, call_next):
    logger.info(f'Incoming request: {request.method} {request.url}')
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f'Error handling request: {e}')
        return JSONResponse({'error': str(e)}, status_code=500)
    logger.info(f'Response status: {response.status_code} for {request.method} {request.url}')
    return response


async def auth_middleware(request: Request, call_next):
    path = request.url.path

    if path == '/user/api/user/login/' and request.method == 'POST':
        return await handle_login(request)
    
    if path == '/user/api/user/refresh/' and request.method == 'POST':
        return await handle_refresh_token(request)
    
    if path == '/user/api/user/logout/' and request.method == 'POST':
        try:
            payload = await verify_jwt(request)
            request.state.user = payload
        except Exception as e:
            logger.error(f'JWT verification failed for logout: {e}')
            return JSONResponse({"detail": str(e)}, status_code=401)
        
        return await handle_logout(request)

    if not is_endpoint_public(path, request.method):
        try:
            payload = await verify_jwt(request)
            request.state.user = payload
            logger.info(f'User set in request.state: {payload}')
        except Exception as e:
            logger.error(f'JWT verification failed: {e}')
            return JSONResponse({"detail": str(e)}, status_code=401)

    response = await call_next(request)
    return response



