import logging
from django.utils.deprecation import MiddlewareMixin
from django.db import connection

logger = logging.getLogger(__name__)


class LoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        logger.debug(f"Request: {request.method} {request.path}")
        return None

    def process_response(self, request, response):
        logger.debug(f"Response: {response.status_code}")
        return response

    def process_exception(self, request, exception):
        logger.error(f"Exception: {exception}", exc_info=True)
        return None


class QueryCountMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.query_count = len(connection.queries)
        return None

    def process_response(self, request, response):
        if hasattr(request, 'query_count'):
            query_count = len(connection.queries) - request.query_count
            logger.debug(f"Number of queries: {query_count}")
        return response
