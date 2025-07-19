from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Genera reporte de rendimiento del sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Número de días para el reporte (default: 7)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='performance_report.json',
            help='Archivo de salida para el reporte'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        output_file = options['output']
        
        self.stdout.write(f'Generando reporte de rendimiento para los últimos {days} días...')
        
        # Estadísticas de base de datos
        db_stats = self.get_database_stats()
        
        # Estadísticas de cache
        cache_stats = self.get_cache_stats()
        
        # Estadísticas de modelos
        model_stats = self.get_model_stats()
        
        # Estadísticas del sistema
        system_stats = self.get_system_stats()
        
        report = {
            'generated_at': timezone.now().isoformat(),
            'period_days': days,
            'database': db_stats,
            'cache': cache_stats,
            'models': model_stats,
            'system': system_stats
        }
        
        # Guardar reporte
        output_path = os.path.join(settings.BASE_DIR, 'reports', output_file)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'Reporte generado exitosamente: {output_path}')
        )
    
    def get_database_stats(self):
        """Obtiene estadísticas de la base de datos"""
        with connection.cursor() as cursor:
            # Para SQLite
            if 'sqlite' in connection.vendor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]
                
                table_stats = {}
                for table in tables:
                    if not table.startswith('django_') and not table.startswith('auth_'):
                        cursor.execute(f"SELECT COUNT(*) FROM {table};")
                        count = cursor.fetchone()[0]
                        table_stats[table] = {'count': count}
                
                return {
                    'vendor': connection.vendor,
                    'tables': table_stats,
                    'total_queries': len(connection.queries)
                }
        
        return {'vendor': connection.vendor}
    
    def get_cache_stats(self):
        """Obtiene estadísticas del cache"""
        try:
            # Intentar obtener estadísticas de Redis
            if hasattr(cache, '_cache') and hasattr(cache._cache, 'get_stats'):
                return cache._cache.get_stats()
            else:
                return {
                    'backend': str(cache.__class__),
                    'status': 'active'
                }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'error'
            }
    
    def get_model_stats(self):
        """Obtiene estadísticas de los modelos"""
        from core.models import Miembro, Contribucion, Grupo, Evento, Certificado
        
        return {
            'miembros': {
                'total': Miembro.objects.count(),
                'activos': Miembro.objects.filter(estado='Activo').count(),
                'inactivos': Miembro.objects.filter(estado='Inactivo').count()
            },
            'contribuciones': {
                'total': Contribucion.objects.count(),
                'este_mes': Contribucion.objects.filter(
                    fecha_contribucion__gte=timezone.now().replace(day=1)
                ).count()
            },
            'grupos': {
                'total': Grupo.objects.count()
            },
            'eventos': {
                'total': Evento.objects.count(),
                'proximos': Evento.objects.filter(
                    fecha_evento__gte=timezone.now().date()
                ).count()
            },
            'certificados': {
                'total': Certificado.objects.count(),
                'emitidos': Certificado.objects.filter(estado='emitido').count()
            }
        }
    
    def get_system_stats(self):
        """Obtiene estadísticas del sistema"""
        import psutil
        import platform
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            }
        }