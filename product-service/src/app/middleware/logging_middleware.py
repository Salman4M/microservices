import time
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from src.app.utils.logging import main_logger, log_request, log_response, log_error, log_gateway_info


async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware to log all incoming requests and responses"""
    
    start_time = time.time()
    
    # Extract request information
    request_data = {
        'method': request.method,
        'url': str(request.url),
        'headers': dict(request.headers),
        'query_params': dict(request.query_params),
        'path_params': dict(request.path_params),
        'client_ip': request.client.host if request.client else 'unknown',
        'user_agent': request.headers.get('user-agent', 'unknown')
    }
    
    # Try to get request body for POST/PUT requests
    try:
        if request.method in ['POST', 'PUT', 'PATCH']:
            body = await request.body()
            if body:
                try:
                    request_data['body'] = json.loads(body.decode())
                except json.JSONDecodeError:
                    request_data['body'] = body.decode()
    except Exception as e:
        request_data['body'] = f"Error reading body: {str(e)}"
    
    # Log the incoming request
    log_request(main_logger, request_data)
    
    # Log gateway-specific information
    log_gateway_info(main_logger, dict(request.headers))
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Calculate response time
        process_time = (time.time() - start_time) * 1000
        
        # Extract response information
        response_data = {
            'status_code': response.status_code,
            'response_time': round(process_time, 2)
        }
        
        # Try to get response body
        try:
            if hasattr(response, 'body'):
                response_data['body'] = json.loads(response.body.decode()) if response.body else {}
        except Exception:
            response_data['body'] = "Could not parse response body"
        
        # Log the response
        log_response(main_logger, response_data)
        
        return response
        
    except Exception as e:
        # Calculate error response time
        process_time = (time.time() - start_time) * 1000
        
        # Log the error
        error_data = {
            'error_type': type(e).__name__,
            'error_message': str(e),
            'traceback': str(e.__traceback__) if hasattr(e, '__traceback__') else 'No traceback',
            'request_info': request_data,
            'response_time': round(process_time, 2)
        }
        
        log_error(main_logger, error_data)
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)}
        )
