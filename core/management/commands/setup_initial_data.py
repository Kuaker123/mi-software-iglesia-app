from django.core.management.base import BaseCommand
from core.models import TipoCertificado, ConfiguracionComunicacion

class Command(BaseCommand):
    help = 'Configura datos iniciales para la aplicación'

    def handle(self, *args, **options):
        # Crear tipos de certificado por defecto
        tipos_certificado = [
            {'nombre': 'Bautismo', 'descripcion': 'Certificado de Bautismo'},
            {'nombre': 'Confirmación', 'descripcion': 'Certificado de Confirmación'},
            {'nombre': 'Matrimonio', 'descripcion': 'Certificado de Matrimonio'},
            {'nombre': 'Membresía', 'descripcion': 'Certificado de Membresía'},
        ]
        
        for tipo_data in tipos_certificado:
            tipo, created = TipoCertificado.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults={'descripcion': tipo_data['descripcion']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Tipo de certificado "{tipo.nombre}" creado exitosamente')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Tipo de certificado "{tipo.nombre}" ya existe')
                )
        
        # Crear configuración de comunicación por defecto
        config, created = ConfiguracionComunicacion.objects.get_or_create(
            id_config=1,
            defaults={
                'servidor_smtp': 'smtp.gmail.com',
                'puerto_smtp': 587,
                'usar_tls': True,
                'usuario_smtp': 'usuario@ejemplo.com',
                'password_smtp': 'password_temporal',
                'email_remitente': 'iglesia@ejemplo.com',
                'nombre_remitente': 'Iglesia',
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Configuración de comunicación creada exitosamente')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Configuración de comunicación ya existe')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n¡Configuración inicial completada!')
        )