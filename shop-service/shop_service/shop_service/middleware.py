import logging
from django.http import HttpResponse

logger = logging.getLogger('shop_service')


class DRFLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f'Request: {request.method} {request.get_full_path()}')
        logger.info(f'Headers: {dict(request.headers)}')
        if request.body:
            try:
                logger.info(f"Body: {request.body.decode('utf-8')}")
            except Exception:
                logger.info("Body: <unreadable>")

        response = self.get_response(request)
        if response is None:
            response = HttpResponse()

        logger.info(f'Response status: {getattr(response, "status_code", "N/A")}')
        try:
            if hasattr(response, 'data'):
                logger.info(f'Response data: {response.data}')
            else:
                logger.info(f'Response content: {getattr(response, "content", b"").decode("utf-8")}')
        except Exception:
            logger.info("Response content: <unreadable>")

        return response
