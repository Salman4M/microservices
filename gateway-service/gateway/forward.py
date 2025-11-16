# gateway/forward.py
import httpx
from fastapi.responses import JSONResponse, Response
from urllib.parse import urlparse
from .services import SERVICE_URLS
from .logging import logger


EXCLUDED_REQUEST_HEADERS = {'host', 'connection', 'content-length', 'accept-encoding', 'cookie', 'referer'}
EXCLUDED_RESPONSE_HEADERS = {'content-encoding', 'transfer-encoding', 'connection'}
DEFAULT_TIMEOUT = 30.0


async def forward_request(service: str, path: str, request):
    if service not in SERVICE_URLS:
        return JSONResponse({'error': 'Unknown service'}, status_code=400)

    url = f'{SERVICE_URLS[service].rstrip("/")}/{path.lstrip("/")}'
    headers = _prepare_headers(request, service)
    body = await request.body()

    logger.info(f"Forwarding request to {url} | Method: {request.method}")

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, verify=False) as client:
            resp = await client.request(
                request.method,
                url,
                headers=headers,
                content=body,
                params=request.query_params
            )

        resp_headers = {k: v for k, v in resp.headers.items() 
                       if k.lower() not in EXCLUDED_RESPONSE_HEADERS}

        logger.info(f'Received {resp.status_code} from {url}')

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=resp_headers,
            media_type=resp.headers.get('content-type'),
        )

    except httpx.RequestError as e:
        logger.error(f'RequestError: {e}')
        return JSONResponse({'error': f'Service unreachable: {e}'}, status_code=503)
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        return JSONResponse({'error': str(e)}, status_code=500)

def _prepare_headers(request, service: str):
    headers = {k.lower(): v for k, v in request.headers.items() 
               if k.lower() not in EXCLUDED_REQUEST_HEADERS}
    auth_header = request.headers.get('Authorization')
    if auth_header:
        headers['authorization'] = auth_header
        logger.info(f'Forwarding with Authorization header: {auth_header}')
    else:
        logger.warning('No Authorization header found')

    user = getattr(request.state, 'user', None)
    if user:
        user_id = user.get('sub') or user.get('user_id')
        if user_id:
            headers['x-user-id'] = str(user_id)
            logger.info(f'Forwarding with X-User-ID: {user_id}')
        else:
            logger.warning('User ID not found in request.state.user')
    else:
        logger.warning('No user in request.state, X-User-ID not set')

    parsed = urlparse(SERVICE_URLS[service])
    headers['host'] = parsed.netloc

    return headers