from django.urls import path
from . import views, auth_views

urlpatterns = [
    # URLs de autenticación
    path('auth/login/', auth_views.login_view, name='login'),
    path('auth/logout/', auth_views.logout_view, name='logout'),
    path('auth/usuarios/', auth_views.gestionar_usuarios, name='gestionar_usuarios'),
    path('auth/usuarios/crear/', auth_views.crear_usuario, name='crear_usuario'),
    path('auth/usuarios/<int:user_id>/toggle/', auth_views.toggle_usuario_estado, name='toggle_usuario_estado'),
    
    # Dashboards por rol
    #path('dashboard/', auth_views.dashboard_view, name='dashboard'),
    path('admin-dashboard/', auth_views.admin_dashboard, name='admin_dashboard'),
    path('editor-dashboard/', auth_views.editor_dashboard, name='editor_dashboard'),
    path('observador-dashboard/', auth_views.observador_dashboard, name='observador_dashboard'),
    
    # URLs existentes...
    path('', views.dashboard, name='dashboard'),
    
    # === NUEVO: DASHBOARD FINANCIERO AVANZADO ===
    path('finanzas/', views.dashboard_financiero, name='dashboard_financiero'),
    path('finanzas/reportes/', views.reportes_financieros, name='reportes_financieros'),
    path('finanzas/exportar/<str:formato>/', views.exportar_finanzas, name='exportar_finanzas'),
    path('finanzas/api/datos-grafico/', views.api_datos_grafico_financiero, name='api_datos_grafico_financiero'),
    
    # Miembros
    path('miembros/', views.listar_miembros, name='listar_miembros'),
    path('miembros/crear/', views.crear_miembro, name='crear_miembro'),
    path('miembros/<int:miembro_id>/', views.detalle_miembro, name='detalle_miembro'),
    path('miembros/<int:miembro_id>/editar/', views.editar_miembro, name='editar_miembro'),
    path('miembros/<int:miembro_id>/eliminar/', views.eliminar_miembro, name='eliminar_miembro'),
    
    # Contribuciones MEJORADAS
    path('contribuciones/', views.listar_contribuciones, name='listar_contribuciones'),
    path('contribuciones/crear/', views.crear_contribucion, name='crear_contribucion'),
    path('contribuciones/<int:contribucion_id>/', views.detalle_contribucion, name='detalle_contribucion'),  # AGREGAR ESTA LÍNEA
    path('contribuciones/<int:contribucion_id>/editar/', views.editar_contribucion, name='editar_contribucion'),
    path('contribuciones/<int:contribucion_id>/eliminar/', views.eliminar_contribucion, name='eliminar_contribucion'),
    path('contribuciones/importar/', views.importar_contribuciones, name='importar_contribuciones'),
    
    # Grupos
    path('grupos/', views.listar_grupos, name='listar_grupos'),
    path('grupos/crear/', views.crear_grupo, name='crear_grupo'),
    path('grupos/<int:grupo_id>/', views.detalle_grupo, name='detalle_grupo'),
    path('grupos/<int:grupo_id>/editar/', views.editar_grupo, name='editar_grupo'),
    path('grupos/<int:grupo_id>/eliminar/', views.eliminar_grupo, name='eliminar_grupo'),
    path('grupos/<int:grupo_id>/remover_miembro/<int:miembro_id>/', views.quitar_miembro_grupo, name='quitar_miembro_grupo'),
    
    # Eventos
    path('eventos/', views.listar_eventos, name='listar_eventos'),
    path('eventos/crear/', views.crear_evento, name='crear_evento'),
    path('eventos/<int:evento_id>/', views.detalle_evento, name='detalle_evento'),
    path('eventos/<int:evento_id>/editar/', views.editar_evento, name='editar_evento'),
    path('eventos/<int:evento_id>/eliminar/', views.eliminar_evento, name='eliminar_evento'),
    path('eventos/<int:evento_id>/asistencia/', views.gestionar_asistencia, name='gestionar_asistencia'),
    path('eventos/<int:evento_id>/registrar_asistencia/', views.registrar_asistencia, name='registrar_asistencia'),
    path('eventos/calendario/', views.calendario_eventos, name='calendario_eventos'),
    
    # Certificados - NUEVO
    path('certificados/', views.listar_certificados, name='listar_certificados'),
    path('certificados/crear/', views.crear_certificado, name='crear_certificado'),
    path('certificados/<int:id_certificado>/', views.detalle_certificado, name='detalle_certificado'),
    path('certificados/<int:id_certificado>/editar/', views.editar_certificado, name='editar_certificado'),
    path('certificados/<int:id_certificado>/eliminar/', views.eliminar_certificado, name='eliminar_certificado'),
    path('certificados/<int:id_certificado>/generar_pdf/', views.generar_pdf_certificado, name='generar_pdf_certificado'),
    path('certificados/<int:id_certificado>/descargar/', views.descargar_certificado, name='descargar_certificado'),
    path('certificados/tipos/', views.gestionar_tipos_certificados, name='gestionar_tipos_certificados'),
    path('certificados/tipos/crear/', views.crear_tipo_certificado, name='crear_tipo_certificado'),
    path('certificados/tipos/<int:id_tipo>/editar/', views.editar_tipo_certificado, name='editar_tipo_certificado'),
    
    # === SISTEMA DE COMUNICACIÓN ===
    # Dashboard de comunicaciones
    path('comunicaciones/', views.dashboard_comunicaciones, name='dashboard_comunicaciones'),
    
    # Listas de distribución
    path('comunicaciones/listas/', views.listar_listas_distribucion, name='listar_listas_distribucion'),
    path('comunicaciones/listas/crear/', views.crear_lista_distribucion, name='crear_lista_distribucion'),
    path('comunicaciones/listas/<int:lista_id>/', views.detalle_lista_distribucion, name='detalle_lista_distribucion'),
    path('comunicaciones/listas/<int:lista_id>/editar/', views.editar_lista_distribucion, name='editar_lista_distribucion'),
    
    # Mensajes
    path('comunicaciones/mensajes/', views.listar_mensajes, name='listar_mensajes'),
    path('comunicaciones/mensajes/crear/', views.crear_mensaje, name='crear_mensaje'),
    path('comunicaciones/mensajes/<int:mensaje_id>/', views.detalle_mensaje, name='detalle_mensaje'),
    path('comunicaciones/mensajes/<int:mensaje_id>/enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    
    # Plantillas de mensajes
    path('comunicaciones/plantillas/', views.listar_plantillas_mensaje, name='listar_plantillas_mensaje'),
    path('comunicaciones/plantillas/crear/', views.crear_plantilla_mensaje, name='crear_plantilla_mensaje'),
    path('comunicaciones/plantillas/<int:plantilla_id>/editar/', views.editar_plantilla_mensaje, name='editar_plantilla_mensaje'),
    path('comunicaciones/plantillas/<int:plantilla_id>/eliminar/', views.eliminar_plantilla_mensaje, name='eliminar_plantilla_mensaje'),
    
    # Notificaciones
    path('comunicaciones/notificaciones/', views.listar_notificaciones, name='listar_notificaciones'),
    path('comunicaciones/notificaciones/crear/', views.crear_notificacion, name='crear_notificacion'),
    path('comunicaciones/notificaciones/<int:notificacion_id>/marcar_leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('comunicaciones/notificaciones/<int:notificacion_id>/eliminar/', views.eliminar_notificacion, name='eliminar_notificacion'),
    
    # Configuración
    path('comunicaciones/configuracion/', views.configuracion_comunicacion, name='configuracion_comunicacion'),
    
    # APIs AJAX
    path('comunicaciones/api/preview-lista/<int:lista_id>/', views.api_preview_lista_distribucion, name='api_preview_lista_distribucion'),
    path('comunicaciones/api/plantilla/<int:plantilla_id>/', views.api_plantilla_mensaje, name='api_plantilla_mensaje'),
]