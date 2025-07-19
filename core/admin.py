from django.contrib import admin
from django.contrib.admin import AdminSite
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import render
from django.db.models import Count, Sum
from .models import (
    Miembro, Grupo, Contribucion, Evento, Certificado, TipoCertificado,
    ConfiguracionComunicacion, ListaDistribucion, Mensaje, PlantillaMensaje,
    Notificacion, SeguimientoEnvio
)

class CustomAdminSite(AdminSite):
    site_header = '⛪ Sistema Iglesia - Administración'
    site_title = 'Sistema Iglesia Admin'
    index_title = '🏠 Panel de Control'
    
    def index(self, request, extra_context=None):
        # Calcular estadísticas
        extra_context = extra_context or {}
        extra_context.update({
            'total_miembros': Miembro.objects.count(),
            'total_grupos': Grupo.objects.count(),
            'total_contribuciones': Contribucion.objects.count(),
            'total_eventos': Evento.objects.count(),
        })
        return super().index(request, extra_context)

custom_admin_site = CustomAdminSite(name='custom_admin')

@admin.register(Miembro)
class MiembroAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'email_display', 'telefono', 'estado_display', 'fecha_ingreso')
    list_filter = ('estado', 'genero', 'fecha_ingreso')
    search_fields = ('nombre', 'apellido', 'email', 'telefono')
    list_per_page = 25
    date_hierarchy = 'fecha_ingreso'
    readonly_fields = ('fecha_ingreso',)
    
    fieldsets = (
        ('👤 Información Personal', {
            'fields': ('nombre', 'apellido', 'fecha_nacimiento', 'genero'),
            'classes': ('wide',)
        }),
        ('📞 Contacto', {
            'fields': ('email', 'telefono', 'direccion'),
            'classes': ('wide',)
        }),
        ('⛪ Membresía', {
            'fields': ('estado',),  # REMOVER fecha_ingreso de aquí
            'classes': ('wide',)
        }),
        ('📅 Información del Sistema', {
            'fields': ('fecha_ingreso',),  # MOVER aquí como solo lectura
            'classes': ('collapse',)
        }),
    )
    
    def nombre_completo(self, obj):
        return format_html(
            '<strong>👤 {} {}</strong>',
            obj.nombre,
            obj.apellido
        )
    nombre_completo.short_description = '👤 Nombre Completo'
    
    def email_display(self, obj):
        if obj.email:
            return format_html(
                '<a href="mailto:{}" style="color: #667eea;">📧 {}</a>',
                obj.email,
                obj.email
            )
        return '📧 Sin email'
    email_display.short_description = '📧 Email'
    
    def estado_display(self, obj):
        if obj.estado == 'Activo':
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✅ Activo</span>'
            )
        elif obj.estado == 'Inactivo':
            return format_html(
                '<span style="color: #ef4444; font-weight: bold;">❌ Inactivo</span>'
            )
        else:
            return format_html(
                '<span style="color: #f59e0b; font-weight: bold;">⏳ Pendiente</span>'
            )
    estado_display.short_description = '📊 Estado'

@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ('nombre_grupo_display', 'lider_display', 'total_miembros', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('nombre_grupo', 'id_lider__nombre', 'id_lider__apellido')
    # Removido filter_horizontal = ('miembros',) porque no existe esa relación directa
    
    fieldsets = (
        ('👥 Información del Grupo', {
            'fields': ('nombre_grupo', 'descripcion'),
            'classes': ('wide',)
        }),
        ('👨‍💼 Liderazgo', {
            'fields': ('id_lider',),
            'classes': ('wide',)
        }),
        ('📍 Ubicación', {
            'fields': ('ubicacion_geografica',),
            'classes': ('wide',)
        }),
    )
    
    def nombre_grupo_display(self, obj):
        return format_html(
            '<strong>👥 {}</strong>',
            obj.nombre_grupo
        )
    nombre_grupo_display.short_description = '👥 Nombre del Grupo'
    
    def lider_display(self, obj):
        if obj.id_lider:
            return format_html(
                '<span style="color: #8b5cf6; font-weight: bold;">👨‍💼 {} {}</span>',
                obj.id_lider.nombre,
                obj.id_lider.apellido
            )
        return '👤 Sin líder'
    lider_display.short_description = '👨‍💼 Líder'
    
    def total_miembros(self, obj):
        # Contar miembros a través de la tabla intermedia MiembroGrupo
        from .models import MiembroGrupo
        count = MiembroGrupo.objects.filter(id_grupo=obj).count()
        return format_html(
            '<span style="background: #f0f9ff; color: #0369a1; padding: 4px 8px; border-radius: 12px; font-weight: bold;">👥 {}</span>',
            count
        )
    total_miembros.short_description = '👥 Total Miembros'

@admin.register(Contribucion)
class ContribucionAdmin(admin.ModelAdmin):
    list_display = ('miembro_display', 'cantidad_display', 'tipo_display', 'fecha_contribucion', 'metodo_pago')
    list_filter = ('tipo_contribucion', 'metodo_pago', 'fecha_contribucion')
    search_fields = ('id_miembro__nombre', 'id_miembro__apellido', 'concepto')
    date_hierarchy = 'fecha_contribucion'
    list_per_page = 25
    
    fieldsets = (
        ('👤 Información del Miembro', {
            'fields': ('id_miembro',),
            'classes': ('wide',)
        }),
        ('💰 Detalles de la Contribución', {
            'fields': ('cantidad', 'tipo_contribucion', 'concepto', 'metodo_pago'),
            'classes': ('wide',)
        }),
        ('📅 Fecha', {
            'fields': ('fecha_contribucion',),
            'classes': ('wide',)
        }),
    )
    
    def miembro_display(self, obj):
        return format_html(
            '<strong>👤 {} {}</strong>',
            obj.id_miembro.nombre,
            obj.id_miembro.apellido
        )
    miembro_display.short_description = '👤 Miembro'
    
    def cantidad_display(self, obj):
        return format_html(
            '<span style="color: #10b981; font-weight: bold; font-size: 1.1em;">💰 ${:,.2f}</span>',
            obj.cantidad
        )
    cantidad_display.short_description = '💰 Cantidad'
    
    def tipo_display(self, obj):
        colors = {
            'Diezmo': '#10b981',
            'Ofrenda': '#3b82f6', 
            'Especial': '#8b5cf6'
        }
        emojis = {
            'Diezmo': '💰',
            'Ofrenda': '🎁',
            'Especial': '⭐'
        }
        color = colors.get(obj.tipo_contribucion, '#64748b')
        emoji = emojis.get(obj.tipo_contribucion, '💵')
        
        return format_html(
            '<span style="background: {}20; color: {}; padding: 4px 8px; border-radius: 12px; font-weight: bold;">{} {}</span>',
            color, color, emoji, obj.tipo_contribucion
        )
    tipo_display.short_description = '🏷️ Tipo'

@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ('nombre_evento_display', 'fecha_display', 'ubicacion', 'estado_display')
    list_filter = ('fecha_evento', 'ubicacion')
    search_fields = ('nombre_evento', 'descripcion', 'ubicacion')
    date_hierarchy = 'fecha_evento'
    
    fieldsets = (
        ('📅 Información del Evento', {
            'fields': ('nombre_evento', 'descripcion'),
            'classes': ('wide',)
        }),
        ('📍 Detalles', {
            'fields': ('fecha_evento', 'ubicacion'),
            'classes': ('wide',)
        }),
    )
    
    def nombre_evento_display(self, obj):
        return format_html(
            '<strong>📅 {}</strong>',
            obj.nombre_evento
        )
    nombre_evento_display.short_description = '📅 Evento'
    
    def fecha_display(self, obj):
        return format_html(
            '<span style="color: #8b5cf6; font-weight: bold;">📅 {}</span>',
            obj.fecha_evento.strftime('%d/%m/%Y')
        )
    fecha_display.short_description = '📅 Fecha'
    
    def estado_display(self, obj):
        from datetime import date
        if obj.fecha_evento < date.today():
            return format_html(
                '<span style="color: #64748b; font-weight: bold;">✅ Finalizado</span>'
            )
        elif obj.fecha_evento == date.today():
            return format_html(
                '<span style="color: #f59e0b; font-weight: bold;">🔥 Hoy</span>'
            )
        else:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">⏰ Próximo</span>'
            )
    estado_display.short_description = '📊 Estado'

@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ('miembro_display', 'tipo_display', 'fecha_emision', 'estado_display', 'acciones')
    list_filter = ('tipo_certificado', 'fecha_emision', 'estado')  # Corregido
    search_fields = ('miembro__nombre', 'miembro__apellido', 'numero_certificado')  # Corregido
    date_hierarchy = 'fecha_emision'
    list_per_page = 25
    
    def miembro_display(self, obj):
        return format_html(
            '<strong>👤 {} {}</strong>',
            obj.miembro.nombre,  # Corregido
            obj.miembro.apellido  # Corregido
        )
    miembro_display.short_description = '👤 Miembro'
    
    def tipo_display(self, obj):
        return format_html(
            '<span style="background: #f0f9ff; color: #0369a1; padding: 4px 8px; border-radius: 12px; font-weight: bold;">📜 {}</span>',
            obj.tipo_certificado.nombre  # Corregido
        )
    tipo_display.short_description = '📜 Tipo'
    
    def estado_display(self, obj):
        colors = {
            'borrador': '#f59e0b',
            'emitido': '#10b981',
            'anulado': '#ef4444'
        }
        emojis = {
            'borrador': '📝',
            'emitido': '✅',
            'anulado': '❌'
        }
        color = colors.get(obj.estado, '#64748b')
        emoji = emojis.get(obj.estado, '📄')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, emoji, obj.get_estado_display()
        )
    estado_display.short_description = '📊 Estado'

    def acciones(self, obj):
        return format_html(
            '<a href="{}" style="background: #10b981; color: white; padding: 4px 8px; border-radius: 6px; text-decoration: none; font-weight: bold;">📄 Ver PDF</a>',
            reverse('generar_certificado_pdf', args=[obj.id_certificado])
        )
    acciones.short_description = '⚙️ Acciones'

@admin.register(PlantillaMensaje)
class PlantillaMensajeAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'fecha_creacion', 'activa')
    list_filter = ('tipo', 'activa', 'fecha_creacion')
    search_fields = ('nombre', 'asunto', 'contenido_html')
    readonly_fields = ('fecha_creacion',)  # Solo fecha_creacion existe
    
    fieldsets = (
        ('📝 Información Básica', {
            'fields': ('nombre', 'descripcion', 'tipo', 'activa'),
            'classes': ('wide',)
        }),
        ('📧 Contenido del Mensaje', {
            'fields': ('asunto', 'contenido_html', 'contenido_texto'),
            'classes': ('wide',)
        }),
        ('🔧 Configuración', {
            'fields': ('variables_disponibles', 'creado_por'),
            'classes': ('collapse',)
        }),
        ('📅 Fechas', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'destinatario', 'tipo', 'leida', 'fecha_creacion')
    list_filter = ('tipo', 'leida', 'fecha_creacion')
    search_fields = ('titulo', 'destinatario__nombre', 'mensaje')  # Corregido
    readonly_fields = ('fecha_creacion', 'fecha_lectura')
    
    fieldsets = (
        ('📢 Información de la Notificación', {
            'fields': ('titulo', 'mensaje', 'tipo'),
            'classes': ('wide',)
        }),
        ('👤 Destinatario', {
            'fields': ('destinatario',),  # Removido email_destinatario
            'classes': ('wide',)
        }),
        ('📊 Estado', {
            'fields': ('leida', 'fecha_lectura', 'mostrar_hasta', 'requiere_accion', 'url_accion'),
            'classes': ('wide',)
        }),
        ('📅 Fechas', {
            'fields': ('fecha_creacion', 'creado_por'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SeguimientoEnvio)
class SeguimientoEnvioAdmin(admin.ModelAdmin):
    list_display = ('mensaje', 'destinatario', 'estado', 'fecha_envio')
    list_filter = ('estado', 'fecha_envio')
    search_fields = ('mensaje__titulo', 'destinatario__nombre', 'email_destinatario')
    readonly_fields = ('fecha_envio', 'fecha_lectura')
    
    fieldsets = (
        ('📧 Información del Envío', {
            'fields': ('mensaje', 'destinatario', 'email_destinatario'),
            'classes': ('wide',)
        }),
        ('📊 Estado del Envío', {
            'fields': ('estado', 'error_detalle'),
            'classes': ('wide',)
        }),
        ('📅 Fechas', {
            'fields': ('fecha_envio', 'fecha_lectura'),
            'classes': ('wide',)
        }),
    )

# Registrar en el admin personalizado
custom_admin_site.register(PlantillaMensaje, PlantillaMensajeAdmin)
custom_admin_site.register(Notificacion, NotificacionAdmin)
custom_admin_site.register(SeguimientoEnvio, SeguimientoEnvioAdmin)
custom_admin_site.register(Miembro, MiembroAdmin)
custom_admin_site.register(Grupo, GrupoAdmin)
custom_admin_site.register(Contribucion, ContribucionAdmin)
custom_admin_site.register(Evento, EventoAdmin)
custom_admin_site.register(Certificado, CertificadoAdmin)
custom_admin_site.register(TipoCertificado)
custom_admin_site.register(ConfiguracionComunicacion)
custom_admin_site.register(ListaDistribucion)
custom_admin_site.register(Mensaje)