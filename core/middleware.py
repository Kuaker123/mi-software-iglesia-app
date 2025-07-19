import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.core.cache import cache
from django.conf import settings

performance_logger = logging.getLogger('performance')
security_logger = logging.getLogger('django.security')

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Middleware para monitorear el rendimiento de las requests"""
    
    def process_request(self, request):
        request.start_time = time.time()
        request.db_queries_start = len(connection.queries)
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            db_queries = len(connection.queries) - getattr(request, 'db_queries_start', 0)
            
            # Log si la request toma más de 1 segundo
            if duration > 1.0:
                performance_logger.warning({
                    'slow_request': True,
                    'path': request.path,
                    'method': request.method,
                    'duration': round(duration, 3),
                    'db_queries': db_queries,
                    'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                    'status_code': response.status_code
                })
            
            # Log estadísticas generales
            performance_logger.info({
                'path': request.path,
                'method': request.method,
                'duration': round(duration, 3),
                'db_queries': db_queries,
                'status_code': response.status_code,
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100]
            })
            
            # Agregar headers de debug en desarrollo
            if settings.DEBUG:
                response['X-Debug-Duration'] = str(round(duration, 3))
                response['X-Debug-DB-Queries'] = str(db_queries)
        
        return response

class SecurityMonitoringMiddleware(MiddlewareMixin):
    """Middleware para monitorear eventos de seguridad"""
    
    def process_request(self, request):
        # Detectar intentos de acceso sospechosos
        suspicious_patterns = [
            '/admin/', '/wp-admin/', '/.env', '/config/',
            'SELECT', 'UNION', 'DROP', 'INSERT', 'UPDATE'
        ]
        
        path = request.path.lower()
        query_string = request.META.get('QUERY_STRING', '').lower()
        
        for pattern in suspicious_patterns:
            if pattern.lower() in path or pattern.lower() in query_string:
                security_logger.warning({
                    'suspicious_request': True,
                    'pattern': pattern,
                    'path': request.path,
                    'query_string': request.META.get('QUERY_STRING', ''),
                    'ip': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
                })
                break
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class CacheStatsMiddleware(MiddlewareMixin):
    """Middleware para estadísticas de cache"""
    
    def process_request(self, request):
        request.cache_hits = 0
        request.cache_misses = 0
    
    def process_response(self, request, response):
        if hasattr(request, 'cache_hits') and hasattr(request, 'cache_misses'):
            total_cache_ops = request.cache_hits + request.cache_misses
            if total_cache_ops > 0:
                hit_rate = (request.cache_hits / total_cache_ops) * 100
                performance_logger.info({
                    'cache_stats': True,
                    'path': request.path,
                    'cache_hits': request.cache_hits,
                    'cache_misses': request.cache_misses,
                    'hit_rate': round(hit_rate, 2)
                })
        
        return response