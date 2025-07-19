from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.utils import timezone
import datetime


# ------------------------------------------------------------------
# Modelo para la tabla 'Miembros'
# ------------------------------------------------------------------
class Miembro(models.Model):
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
        ('Pendiente', 'Pendiente'),
    ]
    
    id_miembro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, db_index=True)
    apellido = models.CharField(max_length=50, db_index=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES)
    email = models.EmailField(
        max_length=100, 
        blank=True, 
        null=True, 
        unique=True,
        validators=[EmailValidator()],
        db_index=True
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_ingreso = models.DateTimeField(auto_now_add=True, db_index=True)
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='Activo',
        db_index=True
    )
    
    class Meta:
        db_table = 'miembros'
        indexes = [
            models.Index(fields=['estado', 'fecha_ingreso']),
            models.Index(fields=['nombre', 'apellido']),
            models.Index(fields=['email']),
            models.Index(fields=['fecha_nacimiento']),
        ]
        verbose_name = 'Miembro'
        verbose_name_plural = 'Miembros'
    
    def calcular_edad(self):
        if self.fecha_nacimiento:
            today = datetime.date.today()
            return today.year - self.fecha_nacimiento.year - ((today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return None
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"

# ------------------------------------------------------------------
# Modelo para la tabla 'Grupos'
# ------------------------------------------------------------------
class Grupo(models.Model):
    id_grupo = models.AutoField(primary_key=True)
    nombre_grupo = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    lider = models.ForeignKey(Miembro, on_delete=models.SET_NULL, null=True, blank=True, related_name='grupos_liderados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'grupos'
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'
    
    def __str__(self):
        return self.nombre_grupo
    
    def total_miembros(self):
        return self.miembrogrupo_set.count()

# ------------------------------------------------------------------
# Modelo para la tabla 'Eventos'
# ------------------------------------------------------------------
class Evento(models.Model):
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]
    
    id_evento = models.AutoField(primary_key=True)
    nombre_evento = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    fecha_evento = models.DateTimeField()
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='programado')
    capacidad_maxima = models.IntegerField(null=True, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'eventos'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        ordering = ['-fecha_evento']
    
    def __str__(self):
        return f"{self.nombre_evento} - {self.fecha_evento.strftime('%Y-%m-%d')}"
    
    def total_asistentes(self):
        return self.asistenciaevento_set.count()

# ------------------------------------------------------------------
# Modelo para Tipos de Certificados
# ------------------------------------------------------------------
class TipoCertificado(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    plantilla_contenido = models.TextField(help_text="Plantilla del contenido del certificado")
    requiere_evento = models.BooleanField(default=False)
    requiere_testigos = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tipos_certificados'
        verbose_name = 'Tipo de Certificado'
        verbose_name_plural = 'Tipos de Certificados'
    
    def __str__(self):
        return self.nombre

# ------------------------------------------------------------------
# Modelo para Contribuciones
# ------------------------------------------------------------------
class Contribucion(models.Model):
    CATEGORIA_CHOICES = [
        ('diezmo', 'Diezmos'),
        ('ofrenda_culto', 'Ofrendas de Culto'),
        ('ofrenda_especial', 'Ofrendas Especiales'),
        ('donacion', 'Donaciones'),
        ('evento', 'Eventos'),
        ('gasto_operativo', 'Gastos Operativos'),
        ('gasto_ministerio', 'Gastos de Ministerio'),
        ('gasto_mantenimiento', 'Mantenimiento'),
    ]
    
    TIPO_CONTRIBUCION_CHOICES = [
        ('diezmo', 'Diezmo'),
        ('ofrenda', 'Ofrenda'),
        ('especial', 'Contribución Especial'),
    ]
    
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta'),
    ]
    
    id_contribucion = models.AutoField(primary_key=True, db_column='id_contribucion')
    id_miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, db_column='id_miembro')
    tipo_contribucion = models.CharField(max_length=50, db_column='tipo_contribucion', choices=TIPO_CONTRIBUCION_CHOICES)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, db_column='cantidad')
    fecha_contribucion = models.DateField(db_column='fecha_contribucion')
    metodo_pago = models.CharField(max_length=50, db_column='metodo_pago', choices=METODO_PAGO_CHOICES, default='efectivo')
    concepto = models.CharField(max_length=200, db_column='concepto', help_text="Descripción detallada del movimiento")
    es_ingreso = models.BooleanField(default=True, db_column='es_ingreso', help_text="True para ingresos, False para egresos")
    categoria = models.CharField(max_length=100, db_column='categoria', choices=CATEGORIA_CHOICES)
    numero_recibo = models.CharField(max_length=50, unique=True, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'contribuciones'
        indexes = [
            models.Index(fields=['fecha_contribucion', 'tipo_contribucion']),
            models.Index(fields=['id_miembro', 'fecha_contribucion']),
        ]
        verbose_name = 'Contribución'
        verbose_name_plural = 'Contribuciones'

# ------------------------------------------------------------------
# Modelo para Certificados
# ------------------------------------------------------------------
class Certificado(models.Model):
    id_certificado = models.AutoField(primary_key=True)
    numero_certificado = models.CharField(max_length=50, unique=True, help_text="Número único del certificado")
    
    # Relaciones
    id_miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, db_column='id_miembro')
    tipo_certificado = models.ForeignKey(TipoCertificado, on_delete=models.CASCADE)
    id_evento = models.ForeignKey(Evento, on_delete=models.SET_NULL, null=True, blank=True, help_text="Evento relacionado (opcional)")
    
    # Fechas
    fecha_emision = models.DateField(auto_now_add=True)
    fecha_evento_certificado = models.DateField(null=True, blank=True, help_text="Fecha del evento certificado (ej: bautismo)")
    
    # Contenido
    contenido_personalizado = models.JSONField(default=dict, help_text="Datos específicos del certificado")
    observaciones = models.TextField(null=True, blank=True)
    
    # Autorización
    pastor_nombre = models.CharField(max_length=200, null=True, blank=True)
    pastor_firma = models.CharField(max_length=200, null=True, blank=True)
    testigo1_nombre = models.CharField(max_length=200, null=True, blank=True)
    testigo2_nombre = models.CharField(max_length=200, null=True, blank=True)
    
    # Archivos
    archivo_pdf = models.FileField(upload_to='certificados/', null=True, blank=True)
    
    # Estado
    estado = models.CharField(max_length=20, choices=[
        ('borrador', 'Borrador'),
        ('emitido', 'Emitido'),
        ('anulado', 'Anulado')
    ], default='borrador')
    
    # Auditoría
    usuario_creacion = models.CharField(max_length=100, null=True, blank=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'certificados'
        indexes = [
            models.Index(fields=['fecha_emision', 'estado']),
            models.Index(fields=['id_miembro', 'tipo_certificado']),
        ]
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'
        ordering = ['-fecha_emision']
    
    def save(self, *args, **kwargs):
        if not self.numero_certificado:
            # Generar número único automáticamente
            year = datetime.datetime.now().year
            count = Certificado.objects.filter(fecha_emision__year=year).count() + 1
            tipo_prefix = self.tipo_certificado.nombre[:3].upper() if self.tipo_certificado else 'CER'
            self.numero_certificado = f"{tipo_prefix}-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_certificado} - {self.id_miembro.nombre} {self.id_miembro.apellido}"

# ------------------------------------------------------------------
# Modelo para Usuarios del Sistema
# ------------------------------------------------------------------
class Usuario(AbstractUser):
    ROLES = [
        ('observador', 'Observador/Visitante'),
        ('editor', 'Editor/Secretario'),
        ('admin', 'Administrador Total')
    ]
    
    # Campos personalizados
    rol = models.CharField(max_length=20, choices=ROLES, default='observador')
    iglesia = models.CharField(max_length=100, default='Mi Iglesia')
    id_miembro = models.ForeignKey(
        Miembro,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='usuario_asociado'
    )
    
    # Campos de auditoría
    fecha_ultimo_acceso = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    creado_por = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'auth_usuarios'
        verbose_name = "Usuario del Sistema"
        verbose_name_plural = "Usuarios del Sistema"
    
    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"
    
    def puede_crear(self):
        """Verifica si el usuario puede crear/editar datos"""
        return self.rol in ['editor', 'admin']
    
    def puede_administrar(self):
        """Verifica si el usuario puede administrar el sistema"""
        return self.rol == 'admin'
    
    def puede_solo_leer(self):
        """Verifica si el usuario solo puede leer"""
        return self.rol == 'observador'

# ------------------------------------------------------------------
# Modelos de Relaciones
# ------------------------------------------------------------------
class MiembroGrupo(models.Model):
    id = models.AutoField(primary_key=True)
    id_miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE, db_column='id_miembro')
    id_grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, db_column='id_grupo')
    fecha_union = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'Miembros_Grupos'
        unique_together = (('id_miembro', 'id_grupo'),)
        verbose_name = "Miembro de Grupo"
        verbose_name_plural = "Miembros de Grupos"

    def __str__(self):
        return f"{self.id_miembro.nombre} {self.id_miembro.apellido} en {self.id_grupo.nombre_grupo}"

class AsistenciaEvento(models.Model):
    id = models.AutoField(primary_key=True)
    id_miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE)
    id_evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    fecha_asistencia = models.DateField()

    class Meta:
        db_table = 'Asistencia_Eventos'
        unique_together = (('id_miembro', 'id_evento'),)
        verbose_name = "Asistencia a Evento"
        verbose_name_plural = "Asistencia a Eventos"

    def __str__(self):
        return f"{self.id_miembro.nombre} asistió a {self.id_evento.nombre_evento}"

# ==================================================================
# SISTEMA DE COMUNICACIÓN
# ==================================================================

class ListaDistribucion(models.Model):
    id_lista = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=[
        ('general', 'General'),
        ('grupo', 'Por Grupo'),
        ('ministerio', 'Por Ministerio'),
        ('evento', 'Por Evento'),
        ('personalizada', 'Personalizada')
    ], default='general')
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.CharField(max_length=100, null=True, blank=True)
    
    # Filtros automáticos
    incluir_grupos = models.ManyToManyField(Grupo, blank=True, related_name='listas_distribucion')
    incluir_solo_activos = models.BooleanField(default=True)
    incluir_solo_con_email = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'Listas_Distribucion'
        verbose_name = "Lista de Distribución"
        verbose_name_plural = "Listas de Distribución"
    
    def __str__(self):
        return self.nombre
    
    def obtener_miembros(self):
        """Obtiene todos los miembros que pertenecen a esta lista"""
        miembros = Miembro.objects.all()
        
        if self.incluir_solo_activos:
            miembros = miembros.filter(estado='Activo')
        
        if self.incluir_solo_con_email:
            miembros = miembros.exclude(email__isnull=True).exclude(email='')
        
        if self.incluir_grupos.exists():
            miembros = miembros.filter(miembrogrupo__id_grupo__in=self.incluir_grupos.all()).distinct()
        
        # Agregar miembros personalizados
        miembros_personalizados = self.miembros_personalizados.all()
        if miembros_personalizados.exists():
            miembros = miembros.union(miembros_personalizados)
        
        return miembros.distinct()

class MiembroListaDistribucion(models.Model):
    id = models.AutoField(primary_key=True)
    lista = models.ForeignKey(ListaDistribucion, on_delete=models.CASCADE, related_name='miembros_personalizados')
    miembro = models.ForeignKey(Miembro, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'Miembros_Listas_Distribucion'
        unique_together = (('lista', 'miembro'),)
        verbose_name = "Miembro en Lista"
        verbose_name_plural = "Miembros en Listas"
    
    def __str__(self):
        return f"{self.miembro} en {self.lista.nombre}"

class Mensaje(models.Model):
    id_mensaje = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    tipo = models.CharField(max_length=50, choices=[
        ('email', 'Correo Electrónico'),
        ('notificacion', 'Notificación Interna'),
        ('anuncio', 'Anuncio General'),
        ('recordatorio', 'Recordatorio')
    ], default='email')
    
    # Configuración de envío
    lista_distribucion = models.ForeignKey(ListaDistribucion, on_delete=models.SET_NULL, null=True, blank=True)
    destinatarios_personalizados = models.ManyToManyField(Miembro, blank=True, related_name='mensajes_recibidos')
    
    # Programación
    fecha_programada = models.DateTimeField(null=True, blank=True, help_text="Dejar vacío para envío inmediato")
    fecha_envio = models.DateTimeField(null=True, blank=True)
    
    # Estado
    estado = models.CharField(max_length=50, choices=[
        ('borrador', 'Borrador'),
        ('programado', 'Programado'),
        ('enviando', 'Enviando'),
        ('enviado', 'Enviado'),
        ('error', 'Error'),
        ('cancelado', 'Cancelado')
    ], default='borrador')
    
    # Configuración de email
    asunto_email = models.CharField(max_length=200, null=True, blank=True)
    es_html = models.BooleanField(default=True)
    adjuntos = models.JSONField(default=list, help_text="Lista de rutas de archivos adjuntos")
    
    # Prioridad
    prioridad = models.CharField(max_length=20, choices=[
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente')
    ], default='normal')
    
    # Auditoría
    creado_por = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    # Estadísticas
    total_destinatarios = models.IntegerField(default=0)
    total_enviados = models.IntegerField(default=0)
    total_errores = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'Mensajes'
        verbose_name = "Mensaje"
        verbose_name_plural = "Mensajes"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} ({self.get_tipo_display()})"
    
    def obtener_destinatarios(self):
        """Obtiene todos los destinatarios del mensaje"""
        destinatarios = set()
        
        if self.lista_distribucion:
            destinatarios.update(self.lista_distribucion.obtener_miembros())
        
        destinatarios.update(self.destinatarios_personalizados.all())
        
        return list(destinatarios)

class SeguimientoEnvio(models.Model):
    id_seguimiento = models.AutoField(primary_key=True)
    mensaje = models.ForeignKey(Mensaje, on_delete=models.CASCADE, related_name='seguimientos')
    destinatario = models.ForeignKey(Miembro, on_delete=models.CASCADE)
    
    # Estado del envío
    estado = models.CharField(max_length=50, choices=[
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('leido', 'Leído'),
        ('error', 'Error'),
        ('rebotado', 'Rebotado')
    ], default='pendiente')
    
    # Detalles del envío
    email_destinatario = models.EmailField()
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    # Errores
    mensaje_error = models.TextField(null=True, blank=True)
    intentos_envio = models.IntegerField(default=0)
    
    # Tracking
    token_seguimiento = models.CharField(max_length=100, unique=True, null=True, blank=True)
    ip_lectura = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'Seguimiento_Envios'
        verbose_name = "Seguimiento de Envío"
        verbose_name_plural = "Seguimiento de Envíos"
        unique_together = (('mensaje', 'destinatario'),)
    
    def __str__(self):
        return f"{self.mensaje.titulo} -> {self.destinatario} ({self.get_estado_display()})"

class PlantillaMensaje(models.Model):
    id_plantilla = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    
    # Contenido
    asunto = models.CharField(max_length=200)
    contenido_html = models.TextField()
    contenido_texto = models.TextField(null=True, blank=True)
    
    # Configuración
    tipo = models.CharField(max_length=50, choices=[
        ('bienvenida', 'Bienvenida'),
        ('evento', 'Evento'),
        ('recordatorio', 'Recordatorio'),
        ('cumpleanos', 'Cumpleaños'),
        ('general', 'General'),
        ('emergencia', 'Emergencia')
    ], default='general')
    
    # Variables disponibles
    variables_disponibles = models.JSONField(default=list, help_text="Lista de variables que se pueden usar en la plantilla")
    
    # Estado
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'Plantillas_Mensajes'
        verbose_name = "Plantilla de Mensaje"
        verbose_name_plural = "Plantillas de Mensajes"
    
    def __str__(self):
        return self.nombre
    
    def renderizar(self, contexto=None):
        """Renderiza la plantilla con el contexto proporcionado"""
        if contexto is None:
            contexto = {}
        
        asunto_renderizado = self.asunto
        contenido_renderizado = self.contenido_html
        
        for variable, valor in contexto.items():
            placeholder = f"{{{{{variable}}}}}"
            asunto_renderizado = asunto_renderizado.replace(placeholder, str(valor))
            contenido_renderizado = contenido_renderizado.replace(placeholder, str(valor))
        
        return asunto_renderizado, contenido_renderizado

class Notificacion(models.Model):
    id_notificacion = models.AutoField(primary_key=True)
    destinatario = models.ForeignKey(Miembro, on_delete=models.CASCADE, related_name='notificaciones')
    
    # Contenido
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=50, choices=[
        ('info', 'Información'),
        ('aviso', 'Aviso'),
        ('recordatorio', 'Recordatorio'),
        ('urgente', 'Urgente'),
        ('cumpleanos', 'Cumpleaños'),
        ('evento', 'Evento')
    ], default='info')
    
    # Estado
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    # Configuración
    mostrar_hasta = models.DateTimeField(null=True, blank=True, help_text="Fecha hasta la cual mostrar la notificación")
    requiere_accion = models.BooleanField(default=False)
    url_accion = models.URLField(null=True, blank=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'Notificaciones'
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.titulo} -> {self.destinatario}"
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            self.leida = True
            self.fecha_lectura = datetime.datetime.now()
            self.save()

class ConfiguracionComunicacion(models.Model):
    id_config = models.AutoField(primary_key=True)
    
    # Configuración de Email
    servidor_smtp = models.CharField(max_length=100, default='smtp.gmail.com')
    puerto_smtp = models.IntegerField(default=587)
    usar_tls = models.BooleanField(default=True)
    email_remitente = models.EmailField()
    nombre_remitente = models.CharField(max_length=100, default='Iglesia')
    
    # Credenciales (se recomienda usar variables de entorno en producción)
    usuario_smtp = models.CharField(max_length=100)
    password_smtp = models.CharField(max_length=100, help_text="Se recomienda usar variables de entorno")
    
    # Configuración de envío
    max_intentos_envio = models.IntegerField(default=3)
    intervalo_entre_envios = models.IntegerField(default=1, help_text="Segundos entre envíos")
    max_destinatarios_por_lote = models.IntegerField(default=50)
    
    # Configuración de notificaciones
    notificaciones_activas = models.BooleanField(default=True)
    dias_mantener_notificaciones = models.IntegerField(default=30)
    
    # Configuración de seguimiento
    habilitar_seguimiento_lectura = models.BooleanField(default=True)
    habilitar_seguimiento_clicks = models.BooleanField(default=True)
    
    # Estado
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'Configuracion_Comunicacion'
        verbose_name = "Configuración de Comunicación"
        verbose_name_plural = "Configuraciones de Comunicación"
    
    def __str__(self):
        return f"Configuración - {self.email_remitente}"
    
    @classmethod
    def obtener_configuracion_activa(cls):
        """Obtiene la configuración activa"""
        return cls.objects.filter(activa=True).first()

# NUEVO MODELO PARA PROYECTOS
class ProyectoFinanciero(models.Model):
    ESTADO_CHOICES = [
        ('planificacion', 'En Planificación'),
        ('activo', 'Activo'),
        ('completado', 'Completado'),
        ('suspendido', 'Suspendido')
    ]
    
    id_proyecto = models.AutoField(primary_key=True)
    nombre_proyecto = models.CharField(max_length=200)
    descripcion = models.TextField()
    meta_financiera = models.DecimalField(max_digits=12, decimal_places=2)
    monto_recaudado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    fecha_inicio = models.DateField()
    fecha_objetivo = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='planificacion')
    responsable = models.ForeignKey(Miembro, on_delete=models.SET_NULL, null=True)
    categoria_proyecto = models.CharField(max_length=100, choices=[
        ('construccion', 'Construcción'),
        ('misiones', 'Misiones'),
        ('equipamiento', 'Equipamiento'),
        ('eventos', 'Eventos Especiales'),
        ('social', 'Acción Social')
    ])
    
    @property
    def porcentaje_completado(self):
        if self.meta_financiera > 0:
            return (self.monto_recaudado / self.meta_financiera) * 100
        return 0
    
    class Meta:
        db_table = 'Proyectos_Financieros'
        verbose_name = 'Proyecto Financiero'
        verbose_name_plural = 'Proyectos Financieros'
    
    def __str__(self):
        return f"{self.numero_certificado} - {self.id_miembro.nombre} {self.id_miembro.apellido}"
    
    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            self.leida = True
            self.fecha_lectura = datetime.datetime.now()
            self.save()

class ConfiguracionComunicacion(models.Model):
    id_config = models.AutoField(primary_key=True)
    
    # Configuración de Email
    servidor_smtp = models.CharField(max_length=100, default='smtp.gmail.com')
    puerto_smtp = models.IntegerField(default=587)
    usar_tls = models.BooleanField(default=True)
    email_remitente = models.EmailField()
    nombre_remitente = models.CharField(max_length=100, default='Iglesia')
    
    # Credenciales (se recomienda usar variables de entorno en producción)
    usuario_smtp = models.CharField(max_length=100)
    password_smtp = models.CharField(max_length=100, help_text="Se recomienda usar variables de entorno")
    
    # Configuración de envío
    max_intentos_envio = models.IntegerField(default=3)
    intervalo_entre_envios = models.IntegerField(default=1, help_text="Segundos entre envíos")
    max_destinatarios_por_lote = models.IntegerField(default=50)
    
    # Configuración de notificaciones
    notificaciones_activas = models.BooleanField(default=True)
    dias_mantener_notificaciones = models.IntegerField(default=30)
    
    # Configuración de seguimiento
    habilitar_seguimiento_lectura = models.BooleanField(default=True)
    habilitar_seguimiento_clicks = models.BooleanField(default=True)
    
    # Estado
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'Configuracion_Comunicacion'
        verbose_name = "Configuración de Comunicación"
        verbose_name_plural = "Configuraciones de Comunicación"
    
    def __str__(self):
        return f"Configuración - {self.email_remitente}"
    
    @classmethod
    def obtener_configuracion_activa(cls):
        """Obtiene la configuración activa"""
        return cls.objects.filter(activa=True).first()

# MODELO DE PRESUPUESTO
class PresupuestoAnual(models.Model):
    año = models.IntegerField()
    categoria = models.CharField(max_length=100)
    monto_presupuestado = models.DecimalField(max_digits=12, decimal_places=2)
    monto_ejecutado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    @property
    def porcentaje_ejecutado(self):
        if self.monto_presupuestado > 0:
            return (self.monto_ejecutado / self.monto_presupuestado) * 100
        return 0
    
    class Meta:
        db_table = 'Presupuestos_Anuales'
        unique_together = ('año', 'categoria')

# MODELO PARA FAMILIAS
class Familia(models.Model):
    nombre_familia = models.CharField(max_length=100)
    jefe_familia = models.ForeignKey(Miembro, on_delete=models.CASCADE, related_name='familia_liderada')
    miembros = models.ManyToManyField(Miembro, related_name='familias')
    meta_diezmo_mensual = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'Familias'
        verbose_name = 'Familia'
        verbose_name_plural = 'Familias'