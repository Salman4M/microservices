from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .logging import logger
from .forward import forward_request
from .middleware import (
    log_requests_middleware,
    auth_middleware,
)
from .openapi import setup_openapi

load_dotenv()

app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    swagger_ui_init_oauth=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.middleware('http')(log_requests_middleware)
app.middleware('http')(auth_middleware)


@app.api_route('/{service}/{full_path:path}', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
async def proxy(service: str, full_path: str, request: Request):
    return await forward_request(service, full_path, request)

setup_openapi(app)


@app.get('/', include_in_schema=False)
def root():
    return {'message': 'API Gateway is running'}

