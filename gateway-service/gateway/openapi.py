import asyncio
import httpx
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from .services import SERVICE_URLS


async def fetch_openapi(service_name: str, url: str, retries: int = 3, delay: int = 2):
	for attempt in range(retries):
		try:
			async with httpx.AsyncClient(timeout=5.0) as client:
				r = await client.get(f'{url}/openapi.json')
				r.raise_for_status()
				data = r.json()
				new_paths = {f'/{service_name}{p}': v for p, v in data.get('paths', {}).items()}
				for path, methods in new_paths.items():
					for method_name, method_data in methods.items():
						method_data['tags'] = [service_name.capitalize()]
				data['paths'] = new_paths
				return data
		except Exception:
			await asyncio.sleep(delay)
	return None


async def merge_openapi_schemas(app: FastAPI):
	merged = get_openapi(title='Gateway API', version='1.0.0', routes=app.routes)
	merged['paths'] = {}

	schemas = await asyncio.gather(
		*[fetch_openapi(name, url) for name, url in SERVICE_URLS.items()]
	)

	for schema in schemas:
		if schema:
			merged['paths'].update(schema.get('paths', {}))
			if 'components' in schema:
				components = merged.setdefault('components', {})
				for key, value in schema['components'].items():
					components.setdefault(key, {}).update(value)

	merged.setdefault('components', {}).setdefault('securitySchemes', {})['BearerAuth'] = {
		'type': 'http',
		'scheme': 'bearer',
		'bearerFormat': 'JWT'
	}
	for path in merged['paths'].values():
		for method in path.values():
			method['security'] = [{'BearerAuth': []}]

	return merged


async def periodic_refresh(app: FastAPI, interval: int = 30):
	while True:
		app.state.merged_openapi_schema = await merge_openapi_schemas(app)
		await asyncio.sleep(interval)


def setup_openapi(app: FastAPI, refresh_interval: int = 30):
	@app.on_event('startup')
	async def startup_event():
		app.state.merged_openapi_schema = await merge_openapi_schemas(app)
		asyncio.create_task(periodic_refresh(app, refresh_interval))

	@app.get('/openapi.json', include_in_schema=False)
	async def custom_openapi():
		if getattr(app.state, 'merged_openapi_schema', None) is None:
			return JSONResponse({'error': 'OpenAPI schema not ready'}, status_code=503)
		return JSONResponse(app.state.merged_openapi_schema)

	app.openapi = lambda: getattr(app.state, 'merged_openapi_schema', None) or {}