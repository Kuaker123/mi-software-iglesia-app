from django import forms
from django.utils import timezone
from .models import (Miembro, Contribucion, Grupo, MiembroGrupo, Evento, AsistenciaEvento, 
                     TipoCertificado, Certificado, ListaDistribucion, MiembroListaDistribucion, 
                     Mensaje, SeguimientoEnvio, PlantillaMensaje, Notificacion, ConfiguracionComunicacion)

class MiembroForm(forms.ModelForm):
    activo = forms.BooleanField(required=False, label='Activo')
    fecha_ingreso_manual = forms.DateTimeField(
        required=False,
        label='Fecha de Ingreso',
        help_text='Fecha de ingreso a la iglesia',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    
    class Meta:
        model = Miembro
        fields = ['nombre', 'apellido', 'fecha_nacimiento', 'genero', 'email', 'telefono', 'direccion', 'estado']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'genero': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verificar email único (excluyendo la instancia actual si es edición)
            queryset = Miembro.objects.filter(email=email)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise forms.ValidationError('Ya existe un miembro con este email.')
        return email

class CertificadoForm(forms.ModelForm):
    class Meta:
        model = Certificado
        fields = ['id_miembro', 'tipo_certificado', 'id_evento', 'fecha_evento_certificado', 'contenido_personalizado', 'observaciones']
        widgets = {
            'fecha_evento_certificado': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'contenido_personalizado': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo miembros activos
        self.fields['id_miembro'].queryset = Miembro.objects.filter(estado='Activo').order_by('nombre', 'apellido')
        # Filtrar solo tipos de certificado activos
        self.fields['tipo_certificado'].queryset = TipoCertificado.objects.filter(activo=True).order_by('nombre')
        self.fields['id_evento'].queryset = Evento.objects.all()
        self.fields['id_evento'].required = False

class FiltroCertificadosForm(forms.Form):
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, número o tipo...',
            'id': 'busqueda'
        })
    )
    tipo_certificado = forms.ModelChoiceField(
        queryset=TipoCertificado.objects.filter(activo=True),
        required=False,
        empty_label="Todos los tipos",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Certificado._meta.get_field('estado').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


# ==================================================================
# FORMULARIOS DEL SISTEMA DE COMUNICACIÓN
# ==================================================================

class ListaDistribucionForm(forms.ModelForm):
    """Formulario para crear y editar listas de distribución"""
    
    class Meta:
        model = ListaDistribucion
        fields = [
            'nombre', 'descripcion', 'tipo', 'incluir_solo_activos', 
            'incluir_solo_con_email', 'incluir_grupos', 'activa'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la lista de distribución'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la lista y su propósito'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'incluir_solo_activos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'incluir_solo_con_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'incluir_grupos': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre de la Lista',
            'descripcion': 'Descripción',
            'tipo': 'Tipo de Lista',
            'incluir_solo_activos': 'Solo miembros activos',
            'incluir_solo_con_email': 'Solo miembros con email',
            'incluir_grupos': 'Grupos a incluir',
            'activa': 'Lista activa',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['incluir_grupos'].queryset = Grupo.objects.all().order_by('nombre_grupo')
        self.fields['incluir_grupos'].required = False

class MensajeForm(forms.ModelForm):
    """Formulario para crear y editar mensajes"""
    
    destinatarios_personalizados = forms.ModelMultipleChoiceField(
        queryset=Miembro.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Destinatarios Específicos'
    )
    
    class Meta:
        model = Mensaje
        fields = [
            'titulo', 'contenido', 'tipo', 'asunto_email', 'lista_distribucion',
            'destinatarios_personalizados', 'prioridad', 'fecha_programada'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del mensaje'
            }),
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Contenido del mensaje...'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'asunto_email': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Asunto del email (solo para emails)'
            }),
            'lista_distribucion': forms.Select(attrs={'class': 'form-control'}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'fecha_programada': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }
        labels = {
            'titulo': 'Título',
            'contenido': 'Contenido',
            'tipo': 'Tipo de Mensaje',
            'asunto_email': 'Asunto del Email',
            'lista_distribucion': 'Lista de Distribución',
            'prioridad': 'Prioridad',
            'fecha_programada': 'Programar Envío',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lista_distribucion'].queryset = ListaDistribucion.objects.filter(activa=True)
        self.fields['lista_distribucion'].empty_label = "Seleccionar lista (opcional)"
        self.fields['lista_distribucion'].required = False
        
        # Solo miembros activos con email para destinatarios personalizados
        self.fields['destinatarios_personalizados'].queryset = Miembro.objects.filter(
            estado='Activo'
        ).exclude(email__isnull=True).exclude(email='').order_by('nombre', 'apellido')
        
        # Hacer asunto_email requerido solo para emails
        self.fields['asunto_email'].required = False
        self.fields['fecha_programada'].required = False

class PlantillaMensajeForm(forms.ModelForm):
    """Formulario para crear y editar plantillas de mensaje"""
    
    variables_disponibles = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nombre, apellido, email, telefono (separadas por comas)'
        }),
        label='Variables Disponibles',
        help_text='Variables que se pueden usar en la plantilla, separadas por comas'
    )
    
    class Meta:
        model = PlantillaMensaje
        fields = [
            'nombre', 'descripcion', 'tipo', 'asunto', 'contenido_html', 
            'contenido_texto', 'variables_disponibles', 'activa'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la plantilla'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción de la plantilla'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'asunto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Asunto del mensaje (puede incluir variables como {{nombre}})'
            }),
            'contenido_html': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Contenido HTML del mensaje...'
            }),
            'contenido_texto': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Contenido en texto plano del mensaje...'
            }),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre de la Plantilla',
            'descripcion': 'Descripción',
            'tipo': 'Tipo de Plantilla',
            'asunto': 'Asunto',
            'contenido_html': 'Contenido HTML',
            'contenido_texto': 'Contenido Texto',
            'activa': 'Plantilla Activa',
        }
    
    def clean_variables_disponibles(self):
        variables = self.cleaned_data.get('variables_disponibles', '')
        if variables:
            # Convertir string separado por comas a lista
            variables_list = [v.strip() for v in variables.split(',') if v.strip()]
            return variables_list
        return []

class NotificacionForm(forms.ModelForm):
    """Formulario para crear notificaciones"""
    
    class Meta:
        model = Notificacion
        fields = [
            'destinatario', 'titulo', 'mensaje', 'tipo',
            'mostrar_hasta', 'requiere_accion', 'url_accion'
        ]
        widgets = {
            'destinatario': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título de la notificación'
            }),
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Mensaje de la notificación...'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'mostrar_hasta': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'requiere_accion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'url_accion': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'URL de la acción (opcional)'
            }),
        }
        labels = {
            'destinatario': 'Destinatario',
            'titulo': 'Título',
            'mensaje': 'Mensaje',
            'tipo': 'Tipo',
            'mostrar_hasta': 'Mostrar Hasta',
            'requiere_accion': 'Requiere Acción',
            'url_accion': 'URL de Acción',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['destinatario'].queryset = Miembro.objects.filter(estado='Activo').order_by('nombre', 'apellido')
        self.fields['mostrar_hasta'].required = False
        self.fields['url_accion'].required = False

class ConfiguracionComunicacionForm(forms.ModelForm):
    """Formulario para configuración del sistema de comunicación"""
    
    class Meta:
        model = ConfiguracionComunicacion
        fields = [
            'servidor_smtp', 'puerto_smtp', 'usar_tls', 'email_remitente',
            'nombre_remitente', 'usuario_smtp', 'password_smtp', 'max_intentos_envio',
            'intervalo_entre_envios', 'max_destinatarios_por_lote', 'notificaciones_activas',
            'habilitar_seguimiento_lectura'
        ]
        widgets = {
            'servidor_smtp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'smtp.gmail.com'
            }),
            'puerto_smtp': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 65535
            }),
            'usar_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_remitente': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'iglesia@ejemplo.com'
            }),
            'nombre_remitente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Iglesia Ejemplo'
            }),
            'usuario_smtp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'usuario@gmail.com'
            }),
            'password_smtp': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña SMTP'
            }),
            'max_intentos_envio': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'intervalo_entre_envios': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.1
            }),
            'max_destinatarios_por_lote': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 1000
            }),
            'notificaciones_activas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'habilitar_seguimiento_lectura': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'servidor_smtp': 'Servidor SMTP',
            'puerto_smtp': 'Puerto SMTP',
            'usar_tls': 'Usar TLS',
            'email_remitente': 'Email Remitente',
            'nombre_remitente': 'Nombre Remitente',
            'usuario_smtp': 'Usuario SMTP',
            'password_smtp': 'Contraseña SMTP',
            'max_intentos_envio': 'Máximo Intentos de Envío',
            'intervalo_entre_envios': 'Intervalo entre Envíos (segundos)',
            'max_destinatarios_por_lote': 'Máximo Destinatarios por Lote',
            'notificaciones_activas': 'Notificaciones Activas',
            'habilitar_seguimiento_lectura': 'Habilitar Seguimiento de Lectura',
        }

# Formularios de filtro para las vistas
class FiltroMensajesForm(forms.Form):
    """Formulario para filtrar mensajes"""
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('borrador', 'Borrador'),
        ('programado', 'Programado'),
        ('enviando', 'Enviando'),
        ('enviado', 'Enviado'),
        ('error', 'Error'),
    ]
    
    TIPO_CHOICES = [
        ('', 'Todos los tipos'),
        ('email', 'Email'),
        ('notificacion', 'Notificación'),
        ('sms', 'SMS'),
    ]
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    busqueda = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título, contenido o asunto...'
        })
    )

class FiltroNotificacionesForm(forms.Form):
    """Formulario para filtrar notificaciones"""
    
    TIPO_CHOICES = [
        ('', 'Todos los tipos'),
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
        ('success', 'Éxito'),
    ]
    
    ESTADO_CHOICES = [
        ('', 'Todas'),
        ('leidas', 'Leídas'),
        ('no_leidas', 'No Leídas'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

# Agregar al final del archivo forms.py, antes de la última línea

class ContribucionForm(forms.ModelForm):
    class Meta:
        model = Contribucion
        fields = ['id_miembro', 'tipo_contribucion', 'cantidad', 'fecha_contribucion', 
                 'metodo_pago', 'concepto', 'es_ingreso', 'categoria', 'numero_recibo', 'observaciones']
        widgets = {
            'fecha_contribucion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'concepto': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['nombre_evento', 'descripcion', 'fecha_evento', 'ubicacion', 
                 'estado', 'capacidad_maxima', 'costo']
        widgets = {
            'fecha_evento': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'nombre_evento': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'capacidad_maxima': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
        }

class FiltroEventosForm(forms.Form):
    busqueda = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    estado = forms.ChoiceField(required=False, choices=[('', 'Todos')] + Evento.ESTADO_CHOICES, 
                              widget=forms.Select(attrs={'class': 'form-control'}))
    fecha_desde = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    fecha_hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

class AsistenciaEventoForm(forms.ModelForm):
    class Meta:
        model = AsistenciaEvento
        fields = ['id_miembro', 'id_evento', 'fecha_asistencia']
        widgets = {
            'fecha_asistencia': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'id_miembro': forms.Select(attrs={'class': 'form-control'}),
            'id_evento': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        evento = kwargs.pop('evento', None)
        super().__init__(*args, **kwargs)
        
        if evento:
            self.fields['id_evento'].initial = evento
            self.fields['id_evento'].widget = forms.HiddenInput()

class GrupoForm(forms.ModelForm):
    class Meta:
        model = Grupo
        fields = ['nombre_grupo', 'descripcion', 'lider', 'activo']
        widgets = {
            'nombre_grupo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'lider': forms.Select(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class MiembroGrupoForm(forms.ModelForm):
    class Meta:
        model = MiembroGrupo
        fields = ['id_miembro', 'id_grupo', 'fecha_union']
        widgets = {
            'id_miembro': forms.Select(attrs={'class': 'form-control'}),
            'id_grupo': forms.Select(attrs={'class': 'form-control'}),
            'fecha_union': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class TipoCertificadoForm(forms.ModelForm):
    class Meta:
        model = TipoCertificado
        fields = ['nombre', 'descripcion', 'plantilla_contenido', 'requiere_evento', 
                 'requiere_testigos', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'plantilla_contenido': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'requiere_evento': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_testigos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }