import asyncio
import httpx
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from .services import SERVICE_URLS
from .logging import logger


async def fetch_openapi(service_name: str, url: str, retries: int = 3, delay: int = 2):
	for attempt in range(retries):
		try:
			async with httpx.AsyncClient(timeout=5.0) as client:
				logger.info(f"Fetching OpenAPI schema from {service_name} at {url}/openapi.json (attempt {attempt + 1}/{retries})")
				r = await client.get(f'{url}/openapi.json')
				r.raise_for_status()
				data = r.json()
				new_paths = {f'/{service_name}{p}': v for p, v in data.get('paths', {}).items()}
				for path, methods in new_paths.items():
					for method_name, method_data in methods.items():
						method_data['tags'] = [service_name.capitalize()]
				data['paths'] = new_paths
				logger.info(f"Successfully fetched OpenAPI schema from {service_name}, found {len(new_paths)} paths")
				return data
		except Exception as e:
			logger.warning(f"Failed to fetch OpenAPI schema from {service_name} at {url}/openapi.json (attempt {attempt + 1}/{retries}): {e}")
			if attempt < retries - 1:
				await asyncio.sleep(delay)
	logger.error(f"Failed to fetch OpenAPI schema from {service_name} after {retries} attempts")
	return None


async def merge_openapi_schemas(app: FastAPI):
	merged = get_openapi(title='Gateway API', version='1.0.0', routes=app.routes)
	merged['paths'] = {}

	logger.info(f"Merging OpenAPI schemas from {len(SERVICE_URLS)} services: {list(SERVICE_URLS.keys())}")
	schemas = await asyncio.gather(
		*[fetch_openapi(name, url) for name, url in SERVICE_URLS.items()]
	)

	for service_name, schema in zip(SERVICE_URLS.keys(), schemas):
		if schema:
			path_count = len(schema.get('paths', {}))
			merged['paths'].update(schema.get('paths', {}))
			if 'components' in schema:
				components = merged.setdefault('components', {})
				for key, value in schema['components'].items():
					components.setdefault(key, {}).update(value)
			logger.info(f"Added {path_count} paths from {service_name} service")
		else:
			logger.warning(f"No schema received from {service_name} service")

	logger.info(f"Total paths in merged schema: {len(merged['paths'])}")

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
		try:
			logger.info("Refreshing OpenAPI schemas...")
			app.state.merged_openapi_schema = await merge_openapi_schemas(app)
			logger.info("OpenAPI schemas refreshed successfully")
		except Exception as e:
			logger.error(f"Error refreshing OpenAPI schemas: {e}", exc_info=True)
		await asyncio.sleep(interval)


def setup_openapi(app: FastAPI, refresh_interval: int = 30):
	@app.on_event('startup')
	async def startup_event():
		logger.info("Starting OpenAPI schema setup...")
		app.state.merged_openapi_schema = await merge_openapi_schemas(app)
		logger.info("OpenAPI schema setup complete")
		asyncio.create_task(periodic_refresh(app, refresh_interval))

	@app.get('/openapi.json', include_in_schema=False)
	async def custom_openapi():
		if getattr(app.state, 'merged_openapi_schema', None) is None:
			return JSONResponse({'error': 'OpenAPI schema not ready'}, status_code=503)
		return JSONResponse(app.state.merged_openapi_schema)

	app.openapi = lambda: getattr(app.state, 'merged_openapi_schema', None) or {}