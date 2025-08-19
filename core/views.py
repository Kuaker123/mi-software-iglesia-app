from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
import json
from decimal import Decimal
from collections import defaultdict
import calendar
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch
from django.contrib.auth.decorators import login_required
from .auth_decorators import admin_required, editor_required, require_role
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

# Importar los modelos y formularios
from .models import (Miembro, Contribucion, Grupo, MiembroGrupo, Evento, AsistenciaEvento, 
                    Certificado, TipoCertificado, ListaDistribucion, MiembroListaDistribucion, 
                    Mensaje, SeguimientoEnvio, PlantillaMensaje, Notificacion, ConfiguracionComunicacion)
from .forms import (AsistenciaEventoForm, CertificadoForm, ConfiguracionComunicacionForm,
                   ContribucionForm, EventoForm, FiltroCertificadosForm,
                   FiltroEventosForm, GrupoForm, ListaDistribucionForm, MensajeForm,
                   MiembroForm, MiembroGrupoForm, NotificacionForm, PlantillaMensajeForm,
                   TipoCertificadoForm)

@login_required
@require_role(['observador', 'editor', 'admin'])
def listar_miembros(request):
    """Lista todos los miembros con filtros y paginación optimizada"""
    # Optimización: usar select_related para evitar N+1 queries
    miembros = Miembro.objects.select_related().all()

    # Filtros
    estado_filtro = request.GET.get('estado', '')
    busqueda = request.GET.get('busqueda', '')

    if estado_filtro:
        miembros = miembros.filter(estado=estado_filtro)

    if busqueda:
        miembros = miembros.filter(
            Q(nombre__icontains=busqueda) |
            Q(apellido__icontains=busqueda) |
            Q(email__icontains=busqueda)
        )

    # Estadísticas optimizadas
    stats = Miembro.objects.aggregate(
        total=Count('id_miembro'),  # Corregido: usar 'id_miembro'
        activos=Count('id_miembro', filter=Q(estado='Activo')),
        inactivos=Count('id_miembro', filter=Q(estado='Inactivo'))
    )

    # Paginación
    paginator = Paginator(miembros, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'miembros': page_obj,
        'stats': stats,
        'estado_filtro': estado_filtro,
        'busqueda': busqueda,
    }

    return render(request, 'core/miembros/listar_miembros.html', context)

@login_required
@editor_required
def crear_miembro(request):
    """Crear nuevo miembro"""
    if request.method == 'POST':
        form = MiembroForm(request.POST)
        if form.is_valid():
            try:
                miembro = form.save()
                messages.success(request, f'Miembro {miembro.nombre} {miembro.apellido} creado exitosamente.')
                return redirect('listar_miembros')
            except Exception as e:
                messages.error(request, f'Error al crear el miembro: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = MiembroForm()
    
    return render(request, 'core/miembros/crear_miembro.html', {'form': form})

def detalle_miembro(request, miembro_id):
    miembro = get_object_or_404(Miembro, pk=miembro_id)
    return render(request, 'core/detalle_miembro.html', {'miembro': miembro})

def editar_miembro(request, miembro_id):
    miembro = get_object_or_404(Miembro, pk=miembro_id)
    if request.method == 'POST':
        form = MiembroForm(request.POST, instance=miembro)
        if form.is_valid():
            form.save()
            return redirect('detalle_miembro', miembro_id=miembro.id_miembro)
    else:
        form = MiembroForm(instance=miembro)
    return render(request, 'core/editar_miembro.html', {'form': form, 'miembro': miembro})

def eliminar_miembro(request, miembro_id):
    miembro = get_object_or_404(Miembro, pk=miembro_id)
    if request.method == 'POST':
        miembro.delete()
        return redirect('listar_miembros')
    return render(request, 'core/eliminar_miembro_confirmar.html', {'miembro': miembro})

# Actualizar la vista listar_contribuciones existente
def listar_contribuciones(request):
    # Obtener todas las contribuciones ordenadas por fecha
    contribuciones = Contribucion.objects.all().order_by('-fecha_contribucion')
    
    # === FILTROS AVANZADOS ===
    tipo_movimiento = request.GET.get('tipo_movimiento', '')
    categoria_filtro = request.GET.get('categoria', '')
    tipo_filtro = request.GET.get('tipo', '')
    mes_filtro = request.GET.get('mes', '')
    año_filtro = request.GET.get('año', '')
    busqueda = request.GET.get('busqueda', '')
    
    if tipo_movimiento:
        es_ingreso = tipo_movimiento == 'ingreso'
        contribuciones = contribuciones.filter(es_ingreso=es_ingreso)
    
    if categoria_filtro:
        contribuciones = contribuciones.filter(categoria=categoria_filtro)
    
    if tipo_filtro:
        contribuciones = contribuciones.filter(tipo_contribucion__iexact=tipo_filtro)
    
    if mes_filtro:
        contribuciones = contribuciones.filter(fecha_contribucion__month=mes_filtro)
    
    if año_filtro:
        contribuciones = contribuciones.filter(fecha_contribucion__year=año_filtro)
    
    if busqueda:
        contribuciones = contribuciones.filter(
            Q(id_miembro__nombre__icontains=busqueda) |
            Q(id_miembro__apellido__icontains=busqueda) |
            Q(concepto__icontains=busqueda) |
            Q(numero_recibo__icontains=busqueda) |
            Q(observaciones__icontains=busqueda)
        )
    
    # === ESTADÍSTICAS MEJORADAS ===
    # Totales generales
    total_ingresos = Contribucion.objects.filter(es_ingreso=True).aggregate(
        total=Sum('cantidad')
    )['total'] or Decimal('0')
    
    total_gastos = Contribucion.objects.filter(es_ingreso=False).aggregate(
        total=Sum('cantidad')
    )['total'] or Decimal('0')
    
    # Totales filtrados
    total_filtrado = contribuciones.aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
    cantidad_registros = contribuciones.count()
    
    # Totales por categoría (solo de los filtrados)
    categorias_resumen = contribuciones.values('categoria', 'es_ingreso').annotate(
        total=Sum('cantidad'),
        cantidad=Count('id_contribucion')
    ).order_by('categoria')
    
    # === PAGINACIÓN ===
    paginator = Paginator(contribuciones, 25)  # 25 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # === OPCIONES PARA FILTROS ===
    categorias_disponibles = Contribucion.objects.values_list(
        'categoria', flat=True
    ).distinct().order_by('categoria')
    
    años_disponibles = Contribucion.objects.dates(
        'fecha_contribucion', 'year', order='DESC'
    )
    
    context = {
        'page_obj': page_obj,
        'contribuciones': page_obj,  # Para compatibilidad
        
        # Estadísticas
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance_general': total_ingresos - total_gastos,
        'total_filtrado': total_filtrado,
        'cantidad_registros': cantidad_registros,
        'categorias_resumen': categorias_resumen,
        
        # Filtros aplicados
        'tipo_movimiento': tipo_movimiento,
        'categoria_filtro': categoria_filtro,
        'tipo_filtro': tipo_filtro,
        'mes_filtro': mes_filtro,
        'año_filtro': año_filtro,
        'busqueda': busqueda,
        
        # Opciones para filtros
        'categorias_disponibles': categorias_disponibles,
        'años_disponibles': años_disponibles,
        'meses': [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ],
    }
    
    return render(request, 'core/listar_contribuciones.html', context)

def crear_contribucion(request):
    if request.method == 'POST':
        form = ContribucionForm(request.POST)
        if form.is_valid():
            contribucion = form.save(commit=False)
            # Si no se especifica fecha, usar la fecha actual
            if not contribucion.fecha_contribucion:
                contribucion.fecha_contribucion = timezone.now().date()
            contribucion.save()
            return redirect('listar_contribuciones')
    else:
        form = ContribucionForm()
        # Establecer fecha actual por defecto
        form.fields['fecha_contribucion'].initial = timezone.now().date()
    
    return render(request, 'core/crear_contribucion.html', {'form': form})

def dashboard(request):
    # Estadísticas básicas
    total_miembros = Miembro.objects.count()
    miembros_activos = Miembro.objects.filter(estado='Activo').count()
    total_contribuciones = Contribucion.objects.count()
    total_grupos = Grupo.objects.count()
    
    # Estadísticas financieras mejoradas
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    # Total de contribuciones del mes
    contribuciones_mes = Contribucion.objects.filter(
        fecha_contribucion__gte=primer_dia_mes,
        fecha_contribucion__lte=hoy
    )
    total_mes = contribuciones_mes.aggregate(total=Sum('cantidad'))['total'] or 0
    
    # Total general de contribuciones
    total_general_contribuciones = Contribucion.objects.aggregate(
        total=Sum('cantidad')
    )['total'] or 0
    
    # Últimas contribuciones
    ultimas_contribuciones = Contribucion.objects.all().order_by('-fecha_contribucion')[:5]
    
    # Últimos miembros registrados
    ultimos_miembros = Miembro.objects.all().order_by('-fecha_ingreso')[:5]
    
    # Últimos grupos creados
    ultimos_grupos = Grupo.objects.all().order_by('-fecha_creacion')[:5]
    
    context = {
        'total_miembros': total_miembros,
        'miembros_activos': miembros_activos,
        'total_contribuciones': total_contribuciones,
        'total_grupos': total_grupos,
        'total_mes': total_mes,
        'total_general_contribuciones': total_general_contribuciones,
        'ultimas_contribuciones': ultimas_contribuciones,
        'ultimos_miembros': ultimos_miembros,
        'ultimos_grupos': ultimos_grupos,
    }
    
    return render(request, 'core/dashboard.html', context)


# ===== GESTIÓN DE GRUPOS =====

def listar_grupos(request):
    grupos = Grupo.objects.all().order_by('nombre_grupo')
    return render(request, 'core/listar_grupos.html', {'grupos': grupos})

def crear_grupo(request):
    if request.method == 'POST':
        form = GrupoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_grupos')
    else:
        form = GrupoForm()
    return render(request, 'core/crear_grupo.html', {'form': form})

def detalle_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)
    miembros_grupo = MiembroGrupo.objects.filter(id_grupo=grupo).select_related('id_miembro')
    
    # Para agregar miembros al grupo
    if request.method == 'POST':
        form = MiembroGrupoForm(request.POST)
        if form.is_valid():
            miembro_grupo = form.save(commit=False)
            miembro_grupo.id_grupo = grupo
            try:
                miembro_grupo.save()
                return redirect('detalle_grupo', grupo_id=grupo.id_grupo)
            except:
                # El miembro ya está en el grupo
                form.add_error('id_miembro', 'Este miembro ya pertenece al grupo.')
    else:
        form = MiembroGrupoForm()
    
    context = {
        'grupo': grupo,
        'miembros_grupo': miembros_grupo,
        'form': form,
    }
    return render(request, 'core/detalle_grupo.html', context)

def editar_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            return redirect('detalle_grupo', grupo_id=grupo.id_grupo)
    else:
        form = GrupoForm(instance=grupo)
    return render(request, 'core/editar_grupo.html', {'form': form, 'grupo': grupo})

def eliminar_grupo(request, grupo_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)
    if request.method == 'POST':
        grupo.delete()
        return redirect('listar_grupos')
    return render(request, 'core/eliminar_grupo_confirmar.html', {'grupo': grupo})

def quitar_miembro_grupo(request, grupo_id, miembro_id):
    grupo = get_object_or_404(Grupo, pk=grupo_id)
    miembro_grupo = get_object_or_404(MiembroGrupo, id_grupo=grupo, id_miembro=miembro_id)
    if request.method == 'POST':
        miembro_grupo.delete()
        return redirect('detalle_grupo', grupo_id=grupo.id_grupo)
    return render(request, 'core/quitar_miembro_grupo_confirmar.html', {
        'grupo': grupo,
        'miembro_grupo': miembro_grupo
    })


# ===== GESTIÓN DE EVENTOS =====

def listar_eventos(request):
    # Obtener todos los eventos ordenados por fecha
    eventos = Evento.objects.all().order_by('-fecha_evento')
    
    # Aplicar filtros
    form = FiltroEventosForm(request.GET)
    if form.is_valid():
        tipo = form.cleaned_data.get('tipo')
        grupo = form.cleaned_data.get('grupo')
        busqueda = form.cleaned_data.get('busqueda')
        
        # Filtro por tipo/fecha
        hoy = timezone.now()
        if tipo == 'proximo':
            eventos = eventos.filter(fecha_evento__gte=hoy)
        elif tipo == 'pasado':
            eventos = eventos.filter(fecha_evento__lt=hoy)
        elif tipo == 'hoy':
            eventos = eventos.filter(
                fecha_evento__date=hoy.date()
            )
        elif tipo == 'semana':
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            eventos = eventos.filter(
                fecha_evento__range=[inicio_semana, fin_semana]
            )
        elif tipo == 'mes':
            eventos = eventos.filter(
                fecha_evento__year=hoy.year,
                fecha_evento__month=hoy.month
            )
        
        # Filtro por grupo
        if grupo:
            eventos = eventos.filter(id_grupo_responsable=grupo)
        
        # Filtro por búsqueda
        if busqueda:
            eventos = eventos.filter(
                Q(nombre_evento__icontains=busqueda) |
                Q(descripcion__icontains=busqueda) |
                Q(ubicacion__icontains=busqueda)
            )
    
    # Estadísticas
    total_eventos = Evento.objects.count()
    eventos_proximos = Evento.objects.filter(fecha_evento__gte=timezone.now()).count()
    eventos_mes = Evento.objects.filter(
        fecha_evento__year=timezone.now().year,
        fecha_evento__month=timezone.now().month
    ).count()
    
    # Agregar información de asistencia a cada evento
    for evento in eventos:
        evento.total_asistentes = AsistenciaEvento.objects.filter(id_evento=evento).count()
    
    context = {
        'eventos': eventos,
        'form': form,
        'total_eventos': total_eventos,
        'eventos_proximos': eventos_proximos,
        'eventos_mes': eventos_mes,
    }
    
    return render(request, 'core/listar_eventos.html', context)

def crear_evento(request):
    if request.method == 'POST':
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save()
            messages.success(request, f'Evento "{evento.nombre_evento}" creado exitosamente.')
            return redirect('detalle_evento', evento_id=evento.id_evento)
    else:
        form = EventoForm()
    
    return render(request, 'core/crear_evento.html', {'form': form})

def detalle_evento(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    asistencias = AsistenciaEvento.objects.filter(id_evento=evento).select_related('id_miembro')
    
    # Estadísticas del evento
    total_asistentes = asistencias.count()
    miembros_activos = Miembro.objects.filter(estado='Activo').count()
    porcentaje_asistencia = (total_asistentes / miembros_activos * 100) if miembros_activos > 0 else 0
    
    # Verificar si el evento ya pasó
    evento_pasado = evento.fecha_evento < timezone.now()
    
    context = {
        'evento': evento,
        'asistencias': asistencias,
        'total_asistentes': total_asistentes,
        'porcentaje_asistencia': round(porcentaje_asistencia, 1),
        'evento_pasado': evento_pasado,
    }
    
    return render(request, 'core/detalle_evento.html', context)

def editar_evento(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    if request.method == 'POST':
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            messages.success(request, f'Evento "{evento.nombre_evento}" actualizado exitosamente.')
            return redirect('detalle_evento', evento_id=evento.id_evento)
    else:
        form = EventoForm(instance=evento)
    
    return render(request, 'core/editar_evento.html', {'form': form, 'evento': evento})

def eliminar_evento(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    if request.method == 'POST':
        nombre_evento = evento.nombre_evento
        evento.delete()
        messages.success(request, f'Evento "{nombre_evento}" eliminado exitosamente.')
        return redirect('listar_eventos')
    
    return render(request, 'core/eliminar_evento_confirmar.html', {'evento': evento})

def gestionar_asistencia(request, evento_id):
    evento = get_object_or_404(Evento, pk=evento_id)
    asistencias = AsistenciaEvento.objects.filter(id_evento=evento).select_related('id_miembro')
    
    if request.method == 'POST':
        form = AsistenciaEventoForm(request.POST, evento=evento)
        if form.is_valid():
            asistencia = form.save(commit=False)
            asistencia.id_evento = evento
            asistencia.fecha_asistencia = timezone.now().date()
            try:
                asistencia.save()
                messages.success(request, f'Asistencia de {asistencia.id_miembro.nombre} registrada exitosamente.')
                return redirect('gestionar_asistencia', evento_id=evento.id_evento)
            except:
                messages.error(request, 'Este miembro ya tiene asistencia registrada para este evento.')
    else:
        form = AsistenciaEventoForm(evento=evento)
    
    context = {
        'evento': evento,
        'asistencias': asistencias,
        'form': form,
        'total_asistentes': asistencias.count(),
    }
    
    return render(request, 'core/gestionar_asistencia.html', context)

def registrar_asistencia(request, evento_id):
    """Vista AJAX para registrar asistencia rápida"""
    if request.method == 'POST':
        evento = get_object_or_404(Evento, pk=evento_id)
        miembro_id = request.POST.get('miembro_id')
        
        if miembro_id:
            miembro = get_object_or_404(Miembro, pk=miembro_id)
            asistencia, created = AsistenciaEvento.objects.get_or_create(
                id_evento=evento,
                id_miembro=miembro,
                defaults={'fecha_asistencia': timezone.now().date()}
            )
            
            if created:
                return JsonResponse({
                    'success': True,
                    'message': f'Asistencia de {miembro.nombre} registrada exitosamente.'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Este miembro ya tiene asistencia registrada.'
                })
    
    return JsonResponse({'success': False, 'message': 'Solicitud inválida.'})

def calendario_eventos(request):
    # Obtener eventos del mes actual y próximo
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1)
    fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    eventos = Evento.objects.filter(
        fecha_evento__range=[inicio_mes, fin_mes]
    ).order_by('fecha_evento')
    
    # Preparar datos para el calendario
    eventos_calendario = []
    for evento in eventos:
        eventos_calendario.append({
            'id': evento.id_evento,
            'title': evento.nombre_evento,
            'start': evento.fecha_evento.isoformat(),
            'url': f'/eventos/{evento.id_evento}/',
            'backgroundColor': '#667eea' if evento.publico else '#6c757d',
            'borderColor': '#667eea' if evento.publico else '#6c757d',
        })
    
    context = {
        'eventos_calendario': eventos_calendario,
        'mes_actual': hoy.strftime('%B %Y'),
    }
    
    return render(request, 'core/calendario_eventos.html', context)


# ===== GESTIÓN DE CERTIFICADOS =====

def listar_certificados(request):
    certificados = Certificado.objects.all().order_by('-fecha_emision')
    
    # Aplicar filtros
    form = FiltroCertificadosForm(request.GET)
    if form.is_valid():
        tipo = form.cleaned_data.get('tipo')
        miembro = form.cleaned_data.get('miembro')
        busqueda = form.cleaned_data.get('busqueda')
        
        if tipo:
            certificados = certificados.filter(tipo_certificado=tipo)
        
        if miembro:
            certificados = certificados.filter(miembro=miembro)
        
        if busqueda:
            certificados = certificados.filter(
                Q(numero_certificado__icontains=busqueda) |
                Q(miembro__nombre__icontains=busqueda) |
                Q(miembro__apellido__icontains=busqueda)
            )
    
    # Estadísticas
    total_certificados = Certificado.objects.count()
    certificados_mes = Certificado.objects.filter(
        fecha_emision__year=timezone.now().year,
        fecha_emision__month=timezone.now().month
    ).count()
    
    context = {
        'certificados': certificados,
        'form': form,
        'total_certificados': total_certificados,
        'certificados_mes': certificados_mes,
    }
    
    return render(request, 'core/listar_certificados.html', context)

@login_required
@editor_required
def crear_certificado(request):
    """Crear nuevo certificado"""
    if request.method == 'POST':
        form = CertificadoForm(request.POST)
        if form.is_valid():
            try:
                certificado = form.save(commit=False)
                certificado.usuario_creacion = request.user.username
                certificado.save()
                
                messages.success(request, f'Certificado creado exitosamente para {certificado.miembro.nombre} {certificado.miembro.apellido}.')
                return redirect('listar_certificados')
            except Exception as e:
                messages.error(request, f'Error al crear el certificado: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CertificadoForm()
    
    return render(request, 'core/certificados/crear_certificado.html', {'form': form})

def detalle_certificado(request, id_certificado):
    certificado = get_object_or_404(Certificado, pk=id_certificado)
    
    context = {
        'certificado': certificado,
    }
    
    return render(request, 'core/detalle_certificado.html', context)

def editar_certificado(request, id_certificado):
    certificado = get_object_or_404(Certificado, pk=id_certificado)
    if request.method == 'POST':
        form = CertificadoForm(request.POST, instance=certificado)
        if form.is_valid():
            form.save()
            messages.success(request, f'Certificado "{certificado.numero_certificado}" actualizado exitosamente.')
            return redirect('detalle_certificado', id_certificado=certificado.id)
    else:
        form = CertificadoForm(instance=certificado)
    
    return render(request, 'core/editar_certificado.html', {'form': form, 'certificado': certificado})

def eliminar_certificado(request, id_certificado):
    certificado = get_object_or_404(Certificado, pk=id_certificado)
    if request.method == 'POST':
        numero_certificado = certificado.numero_certificado
        certificado.delete()
        messages.success(request, f'Certificado "{numero_certificado}" eliminado exitosamente.')
        return redirect('listar_certificados')
    
    return render(request, 'core/eliminar_certificado_confirmar.html', {'certificado': certificado})

def generar_pdf_certificado(request, id_certificado):
    certificado = get_object_or_404(Certificado, pk=id_certificado)
    
    # Crear respuesta HTTP con tipo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="certificado_{certificado.numero_certificado}.pdf"'
    
    # Crear el PDF
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Título
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredText(width/2, height-100, "CERTIFICADO")
    
    # Número de certificado
    p.setFont("Helvetica", 12)
    p.drawCentredText(width/2, height-130, f"No. {certificado.numero_certificado}")
    
    # Contenido principal
    p.setFont("Helvetica", 16)
    p.drawCentredText(width/2, height-200, "Se certifica que:")
    
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredText(width/2, height-250, f"{certificado.miembro.nombre} {certificado.miembro.apellido}")
    
    # Descripción
    p.setFont("Helvetica", 14)
    y_position = height - 300
    lines = certificado.contenido.split('\n')
    for line in lines:
        p.drawCentredText(width/2, y_position, line)
        y_position -= 20
    
    # Fecha y autorización
    p.setFont("Helvetica", 12)
    p.drawCentredText(width/2, height-450, f"Fecha de emisión: {certificado.fecha_emision.strftime('%d/%m/%Y')}")
    
    if certificado.autorizado_por:
        p.drawCentredText(width/2, height-480, f"Autorizado por: {certificado.autorizado_por}")
    
    p.showPage()
    p.save()
    
    return response

def descargar_certificado(request, id_certificado):
    certificado = get_object_or_404(Certificado, pk=id_certificado)
    
    # Crear respuesta HTTP con tipo PDF para descarga
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificado_{certificado.numero_certificado}.pdf"'
    
    # Reutilizar la lógica de generación de PDF
    return generar_pdf_certificado(request, id_certificado)

def gestionar_tipos_certificados(request):
    tipos = TipoCertificado.objects.all().order_by('nombre')
    
    context = {
        'tipos': tipos,
    }
    
    return render(request, 'core/gestionar_tipos_certificados.html', context)

def crear_tipo_certificado(request):
    if request.method == 'POST':
        form = TipoCertificadoForm(request.POST)
        if form.is_valid():
            tipo = form.save()
            messages.success(request, f'Tipo de certificado "{tipo.nombre}" creado exitosamente.')
            return redirect('gestionar_tipos_certificados')
    else:
        form = TipoCertificadoForm()
    
    return render(request, 'core/crear_tipo_certificado.html', {'form': form})

def editar_tipo_certificado(request, id_tipo):
    tipo = get_object_or_404(TipoCertificado, pk=id_tipo)
    if request.method == 'POST':
        form = TipoCertificadoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, f'Tipo de certificado "{tipo.nombre}" actualizado exitosamente.')
            return redirect('gestionar_tipos_certificados')
    else:
        form = TipoCertificadoForm(instance=tipo)
    
    return render(request, 'core/editar_tipo_certificado.html', {'form': form, 'tipo': tipo})

def eliminar_tipo_certificado(request, id_tipo):
    tipo = get_object_or_404(TipoCertificado, pk=id_tipo)
    if request.method == 'POST':
        nombre_tipo = tipo.nombre
        try:
            tipo.delete()
            messages.success(request, f'Tipo de certificado "{nombre_tipo}" eliminado exitosamente.')
        except Exception as e:
            messages.error(request, f'No se puede eliminar el tipo "{nombre_tipo}" porque está en uso.')
        return redirect('gestionar_tipos_certificados')
    
    return render(request, 'core/eliminar_tipo_certificado_confirmar.html', {'tipo': tipo})

def calendario_eventos(request):
    eventos = Evento.objects.all()
    
    # Convertir eventos a formato JSON para el calendario
    eventos_json = []
    for evento in eventos:
        eventos_json.append({
            'id': evento.id_evento,
            'title': evento.nombre_evento,
            'start': evento.fecha_evento.isoformat(),
            'description': evento.descripcion,
            'location': evento.ubicacion,
        })
    
    context = {
        'eventos_json': eventos_json,
    }
    
    return render(request, 'core/calendario_eventos.html', context)



# === DASHBOARD FINANCIERO AVANZADO ===
def dashboard_financiero(request):
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    primer_dia_año = hoy.replace(month=1, day=1)
    
    # === TOTALES GENERALES ===
    total_ingresos = Contribucion.objects.filter(es_ingreso=True).aggregate(
        total=Sum('cantidad')
    )['total'] or Decimal('0')
    
    total_gastos = Contribucion.objects.filter(es_ingreso=False).aggregate(
        total=Sum('cantidad')
    )['total'] or Decimal('0')
    
    balance_general = total_ingresos - total_gastos
    
    # === TOTALES DEL MES ACTUAL ===
    ingresos_mes = Contribucion.objects.filter(
        es_ingreso=True,
        fecha_contribucion__gte=primer_dia_mes,
        fecha_contribucion__lte=hoy
    ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
    
    gastos_mes = Contribucion.objects.filter(
        es_ingreso=False,
        fecha_contribucion__gte=primer_dia_mes,
        fecha_contribucion__lte=hoy
    ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
    
    balance_mes = ingresos_mes - gastos_mes
    
    # === TOTALES DEL AÑO ===
    ingresos_año = Contribucion.objects.filter(
        es_ingreso=True,
        fecha_contribucion__gte=primer_dia_año,
        fecha_contribucion__lte=hoy
    ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
    
    gastos_año = Contribucion.objects.filter(
        es_ingreso=False,
        fecha_contribucion__gte=primer_dia_año,
        fecha_contribucion__lte=hoy
    ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
    
    balance_año = ingresos_año - gastos_año
    
    # === ANÁLISIS POR CATEGORÍAS ===
    categorias_ingresos = Contribucion.objects.filter(
        es_ingreso=True
    ).values('categoria').annotate(
        total=Sum('cantidad'),
        cantidad_movimientos=Count('id_contribucion')
    ).order_by('-total')[:10]
    
    categorias_gastos = Contribucion.objects.filter(
        es_ingreso=False
    ).values('categoria').annotate(
        total=Sum('cantidad'),
        cantidad_movimientos=Count('id_contribucion')
    ).order_by('-total')[:10]
    
    # === MOVIMIENTOS RECIENTES ===
    movimientos_recientes = Contribucion.objects.all().order_by(
        '-fecha_contribucion', '-id_contribucion'
    )[:15]
    
    # === DATOS PARA GRÁFICOS ===
    meses_data = []
    for i in range(12):
        fecha_mes = (hoy.replace(day=1) - timedelta(days=30*i)).replace(day=1)
        if fecha_mes.month == 12:
            ultimo_dia = fecha_mes.replace(year=fecha_mes.year+1, month=1, day=1) - timedelta(days=1)
        else:
            ultimo_dia = fecha_mes.replace(month=fecha_mes.month+1, day=1) - timedelta(days=1)
        
        ingresos_mes_data = Contribucion.objects.filter(
            es_ingreso=True,
            fecha_contribucion__gte=fecha_mes,
            fecha_contribucion__lte=ultimo_dia
        ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
        
        gastos_mes_data = Contribucion.objects.filter(
            es_ingreso=False,
            fecha_contribucion__gte=fecha_mes,
            fecha_contribucion__lte=ultimo_dia
        ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
        
        meses_data.append({
            'mes': calendar.month_name[fecha_mes.month],
            'año': fecha_mes.year,
            'ingresos': float(ingresos_mes_data),
            'gastos': float(gastos_mes_data),
            'balance': float(ingresos_mes_data - gastos_mes_data)
        })
    
    meses_data.reverse()
    
    # === ALERTAS FINANCIERAS ===
    alertas = []
    
    if gastos_mes > ingresos_mes:
        alertas.append({
            'tipo': 'danger',
            'icono': 'fas fa-exclamation-triangle',
            'mensaje': f'Los gastos del mes (${gastos_mes:,.2f}) superan los ingresos (${ingresos_mes:,.2f})'
        })
    
    if balance_general < 0:
        alertas.append({
            'tipo': 'warning',
            'icono': 'fas fa-chart-line-down',
            'mensaje': f'El balance general es negativo: ${balance_general:,.2f}'
        })
    
    hace_semana = hoy - timedelta(days=7)
    movimientos_semana = Contribucion.objects.filter(
        fecha_contribucion__gte=hace_semana
    ).count()
    
    if movimientos_semana == 0:
        alertas.append({
            'tipo': 'info',
            'icono': 'fas fa-info-circle',
            'mensaje': 'No se han registrado movimientos financieros en los últimos 7 días'
        })
    
    # === MÉTRICAS AVANZADAS ===
    promedio_ingreso_mensual = Contribucion.objects.filter(
        es_ingreso=True
    ).aggregate(promedio=Avg('cantidad'))['promedio'] or Decimal('0')
    
    promedio_gasto_mensual = Contribucion.objects.filter(
        es_ingreso=False
    ).aggregate(promedio=Avg('cantidad'))['promedio'] or Decimal('0')
    
    # Top 5 contribuyentes del mes
    top_contribuyentes = Contribucion.objects.filter(
        es_ingreso=True,
        fecha_contribucion__gte=primer_dia_mes,
        fecha_contribucion__lte=hoy
    ).values(
        'id_miembro__nombre', 'id_miembro__apellido'
    ).annotate(
        total_contribuido=Sum('cantidad'),
        cantidad_contribuciones=Count('id_contribucion')
    ).order_by('-total_contribuido')[:5]
    
    context = {
        # Totales generales
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance_general': balance_general,
        
        # Totales del mes
        'ingresos_mes': ingresos_mes,
        'gastos_mes': gastos_mes,
        'balance_mes': balance_mes,
        
        # Totales del año
        'ingresos_año': ingresos_año,
        'gastos_año': gastos_año,
        'balance_año': balance_año,
        
        # Análisis por categorías
        'categorias_ingresos': categorias_ingresos,
        'categorias_gastos': categorias_gastos,
        
        # Movimientos y datos
        'movimientos_recientes': movimientos_recientes,
        'meses_data': json.dumps(meses_data),
        'alertas': alertas,
        
        # Métricas avanzadas
        'promedio_ingreso_mensual': promedio_ingreso_mensual,
        'promedio_gasto_mensual': promedio_gasto_mensual,
        'top_contribuyentes': top_contribuyentes,
        
        # Información adicional
        'fecha_actual': hoy,
        'mes_actual': calendar.month_name[hoy.month],
        'año_actual': hoy.year,
    }
    
    return render(request, 'core/dashboard_financiero.html', context)

# === API PARA GRÁFICOS DINÁMICOS ===
def api_datos_grafico_financiero(request):
    periodo = request.GET.get('periodo', '12')  # meses
    tipo = request.GET.get('tipo', 'mensual')  # mensual, semanal, anual
    
    hoy = timezone.now().date()
    datos = []
    
    if tipo == 'mensual':
        for i in range(int(periodo)):
            fecha_mes = (hoy.replace(day=1) - timedelta(days=30*i)).replace(day=1)
            if fecha_mes.month == 12:
                ultimo_dia = fecha_mes.replace(year=fecha_mes.year+1, month=1, day=1) - timedelta(days=1)
            else:
                ultimo_dia = fecha_mes.replace(month=fecha_mes.month+1, day=1) - timedelta(days=1)
            
            ingresos = Contribucion.objects.filter(
                es_ingreso=True,
                fecha_contribucion__gte=fecha_mes,
                fecha_contribucion__lte=ultimo_dia
            ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
            
            gastos = Contribucion.objects.filter(
                es_ingreso=False,
                fecha_contribucion__gte=fecha_mes,
                fecha_contribucion__lte=ultimo_dia
            ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
            
            datos.append({
                'periodo': f"{calendar.month_name[fecha_mes.month]} {fecha_mes.year}",
                'ingresos': float(ingresos),
                'gastos': float(gastos),
                'balance': float(ingresos - gastos)
            })
    
    datos.reverse()
    return JsonResponse({'datos': datos})

# === EXPORTACIÓN DE REPORTES ===
def exportar_finanzas(request, formato):
    # Obtener filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    tipo_movimiento = request.GET.get('tipo_movimiento')
    categoria = request.GET.get('categoria')
    
    # Filtrar contribuciones
    contribuciones = Contribucion.objects.all().order_by('-fecha_contribucion')
    
    if fecha_inicio:
        contribuciones = contribuciones.filter(fecha_contribucion__gte=fecha_inicio)
    if fecha_fin:
        contribuciones = contribuciones.filter(fecha_contribucion__lte=fecha_fin)
    if tipo_movimiento:
        es_ingreso = tipo_movimiento == 'ingreso'
        contribuciones = contribuciones.filter(es_ingreso=es_ingreso)
    if categoria:
        contribuciones = contribuciones.filter(categoria=categoria)
    
    if formato == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="reporte_financiero.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Fecha', 'Miembro', 'Tipo', 'Categoría', 'Concepto', 
            'Cantidad', 'Método Pago', 'Recibo', 'Observaciones'
        ])
        
        for contrib in contribuciones:
            writer.writerow([
                contrib.fecha_contribucion,
                f"{contrib.id_miembro.nombre} {contrib.id_miembro.apellido}",
                'Ingreso' if contrib.es_ingreso else 'Gasto',
                contrib.get_categoria_display(),
                contrib.concepto,
                contrib.cantidad,
                contrib.get_metodo_pago_display(),
                contrib.numero_recibo or '',
                contrib.observaciones or ''
            ])
        
        return response
    
    elif formato == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_financiero.pdf"'
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        normal_style = styles['Normal']
        
        # Contenido
        story = []
        
        # Título
        title = Paragraph("Reporte Financiero - Iglesia", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Resumen
        total_ingresos = contribuciones.filter(es_ingreso=True).aggregate(
            total=Sum('cantidad')
        )['total'] or Decimal('0')
        
        total_gastos = contribuciones.filter(es_ingreso=False).aggregate(
            total=Sum('cantidad')
        )['total'] or Decimal('0')
        
        resumen_data = [
            ['Concepto', 'Monto'],
            ['Total Ingresos', f'${total_ingresos:,.2f}'],
            ['Total Gastos', f'${total_gastos:,.2f}'],
            ['Balance', f'${total_ingresos - total_gastos:,.2f}']
        ]
        
        resumen_table = Table(resumen_data)
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(resumen_table)
        story.append(Spacer(1, 20))
        
        # Tabla de movimientos
        data = [['Fecha', 'Miembro', 'Tipo', 'Concepto', 'Cantidad']]
        
        for contrib in contribuciones[:50]:  # Limitar a 50 registros
            data.append([
                contrib.fecha_contribucion.strftime('%d/%m/%Y'),
                f"{contrib.id_miembro.nombre} {contrib.id_miembro.apellido}"[:20],
                'Ingreso' if contrib.es_ingreso else 'Gasto',
                contrib.concepto[:30],
                f'${contrib.cantidad:,.2f}'
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response

# === VISTA MEJORADA PARA LISTAR CONTRIBUCIONES ===
def listar_contribuciones(request):
    # Obtener todas las contribuciones ordenadas por fecha
    contribuciones = Contribucion.objects.all().order_by('-fecha_contribucion')
    
    # === FILTROS AVANZADOS ===
    tipo_movimiento = request.GET.get('tipo_movimiento', '')
    categoria_filtro = request.GET.get('categoria', '')
    tipo_filtro = request.GET.get('tipo', '')
    mes_filtro = request.GET.get('mes', '')
    año_filtro = request.GET.get('año', '')
    busqueda = request.GET.get('busqueda', '')
    
    if tipo_movimiento:
        es_ingreso = tipo_movimiento == 'ingreso'
        contribuciones = contribuciones.filter(es_ingreso=es_ingreso)
    
    if categoria_filtro:
        contribuciones = contribuciones.filter(categoria=categoria_filtro)
    
    if tipo_filtro:
        contribuciones = contribuciones.filter(tipo_contribucion__iexact=tipo_filtro)
    
    if mes_filtro:
        contribuciones = contribuciones.filter(fecha_contribucion__month=mes_filtro)
    
    if año_filtro:
        contribuciones = contribuciones.filter(fecha_contribucion__year=año_filtro)
    
    if busqueda:
        contribuciones = contribuciones.filter(
            Q(id_miembro__nombre__icontains=busqueda) |
            Q(id_miembro__apellido__icontains=busqueda) |
            Q(concepto__icontains=busqueda) |
            Q(numero_recibo__icontains=busqueda) |
            Q(observaciones__icontains=busqueda)
        )
    
    # === ESTADÍSTICAS MEJORADAS ===
    total_ingresos = Contribucion.objects.filter(es_ingreso=True).aggregate(
        total=Sum('cantidad')
    )['total'] or Decimal('0')
    
    total_gastos = Contribucion.objects.filter(es_ingreso=False).aggregate(
        total=Sum('cantidad')
    )['total'] or Decimal('0')
    
    # Totales filtrados
    total_filtrado = contribuciones.aggregate(total=Sum('cantidad'))['total'] or Decimal('0')
    cantidad_registros = contribuciones.count()
    
    # Totales por categoría (solo de los filtrados)
    categorias_resumen = contribuciones.values('categoria', 'es_ingreso').annotate(
        total=Sum('cantidad'),
        cantidad=Count('id_contribucion')
    ).order_by('categoria')
    
    # === PAGINACIÓN ===
    paginator = Paginator(contribuciones, 25)  # 25 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # === OPCIONES PARA FILTROS ===
    categorias_disponibles = Contribucion.objects.values_list(
        'categoria', flat=True
    ).distinct().order_by('categoria')
    
    años_disponibles = Contribucion.objects.dates(
        'fecha_contribucion', 'year', order='DESC'
    )
    
    context = {
        'page_obj': page_obj,
        'contribuciones': page_obj,  # Para compatibilidad
        
        # Estadísticas
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance_general': total_ingresos - total_gastos,
        'total_filtrado': total_filtrado,
        'cantidad_registros': cantidad_registros,
        'categorias_resumen': categorias_resumen,
        
        # Filtros aplicados
        'tipo_movimiento': tipo_movimiento,
        'categoria_filtro': categoria_filtro,
        'tipo_filtro': tipo_filtro,
        'mes_filtro': mes_filtro,
        'año_filtro': año_filtro,
        'busqueda': busqueda,
        
        # Opciones para filtros
        'categorias_disponibles': categorias_disponibles,
        'años_disponibles': años_disponibles,
        'meses': [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
        ],
        'metodos_pago': [
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia'),
            ('cheque', 'Cheque'),
            ('tarjeta', 'Tarjeta'),
        ],
    }
    
    return render(request, 'core/listar_contribuciones.html', context)

# === NUEVAS VISTAS CRUD PARA CONTRIBUCIONES ===
def detalle_contribucion(request, contribucion_id):
    """Vista para mostrar detalles de una contribución específica"""
    contribucion = get_object_or_404(Contribucion, pk=contribucion_id)
    
    context = {
        'contribucion': contribucion,
        'miembro': contribucion.id_miembro,
    }
    
    return render(request, 'core/detalle_contribucion.html', context)


def editar_contribucion(request, contribucion_id):
    contribucion = get_object_or_404(Contribucion, pk=contribucion_id)
    if request.method == 'POST':
        form = ContribucionForm(request.POST, instance=contribucion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contribución actualizada exitosamente.')
            return redirect('listar_contribuciones')
    else:
        form = ContribucionForm(instance=contribucion)
    
    return render(request, 'core/editar_contribucion.html', {
        'form': form, 
        'contribucion': contribucion
    })

def eliminar_contribucion(request, contribucion_id):
    contribucion = get_object_or_404(Contribucion, pk=contribucion_id)
    if request.method == 'POST':
        contribucion.delete()
        messages.success(request, 'Contribución eliminada exitosamente.')
        return redirect('listar_contribuciones')
    
    return render(request, 'core/eliminar_contribucion_confirmar.html', {
        'contribucion': contribucion
    })

# === REPORTES FINANCIEROS ===
def reportes_financieros(request):
    hoy = timezone.now().date()
    
    # Reportes predefinidos
    reportes = {
        'mensual': {
            'nombre': 'Reporte Mensual',
            'descripcion': 'Ingresos y gastos del mes actual',
            'icono': 'fas fa-calendar-alt'
        },
        'anual': {
            'nombre': 'Reporte Anual',
            'descripcion': 'Resumen financiero del año',
            'icono': 'fas fa-chart-bar'
        },
        'contribuyentes': {
            'nombre': 'Top Contribuyentes',
            'descripcion': 'Miembros con mayores contribuciones',
            'icono': 'fas fa-users'
        },
        'categorias': {
            'nombre': 'Análisis por Categorías',
            'descripcion': 'Distribución de ingresos y gastos',
            'icono': 'fas fa-chart-pie'
        }
    }
    
    return render(request, 'core/reportes_financieros.html', {
        'reportes': reportes,
        'fecha_actual': hoy
    })


def importar_contribuciones(request):
    """Vista para importar contribuciones desde archivo CSV"""
    if request.method == 'POST':
        archivo_csv = request.FILES.get('archivo_csv')
        if archivo_csv:
            try:
                # Leer el archivo CSV
                
                # Decodificar el archivo
                archivo_texto = archivo_csv.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(archivo_texto))
                
                contribuciones_creadas = 0
                errores = []
                
                for fila_num, fila in enumerate(csv_reader, start=2):
                    try:
                        # Buscar el miembro
                        miembro = Miembro.objects.get(id=fila['miembro_id'])
                        
                        # Convertir fecha
                        fecha = datetime.strptime(fila['fecha_contribucion'], '%d/%m/%Y').date()
                        
                        # Crear la contribución
                        contribucion = Contribucion.objects.create(
                            id_miembro=miembro,
                            cantidad=float(fila['cantidad']),
                            tipo_contribucion=fila['tipo_contribucion'],
                            fecha_contribucion=fecha,
                            categoria=fila.get('categoria', 'Ingreso'),
                            metodo_pago=fila.get('metodo_pago', 'Efectivo'),
                            concepto=fila.get('concepto', ''),
                            descripcion=fila.get('descripcion', '')
                        )
                        contribuciones_creadas += 1
                        
                    except Exception as e:
                        errores.append(f"Fila {fila_num}: {str(e)}")
                
                if errores:
                    messages.warning(request, f"Se importaron {contribuciones_creadas} contribuciones con {len(errores)} errores.")
                    for error in errores[:5]:  # Mostrar solo los primeros 5 errores
                        messages.error(request, error)
                else:
                    messages.success(request, f"Se importaron exitosamente {contribuciones_creadas} contribuciones.")
                    
                return redirect('listar_contribuciones')
                
            except Exception as e:
                messages.error(request, f"Error al procesar el archivo: {str(e)}")
        else:
            messages.error(request, "Por favor selecciona un archivo CSV.")
    
    return render(request, 'core/importar_contribuciones.html')

# ==================================================================
# SISTEMA DE COMUNICACIÓN - VISTAS
# ==================================================================

# ------------------------------------------------------------------
# Dashboard de Comunicaciones
# ------------------------------------------------------------------
def dashboard_comunicaciones(request):
    """Dashboard principal del sistema de comunicaciones"""
    # Estadísticas generales
    total_mensajes = Mensaje.objects.count()
    mensajes_enviados = Mensaje.objects.filter(estado='enviado').count()
    mensajes_pendientes = Mensaje.objects.filter(estado__in=['borrador', 'programado']).count()
    total_listas = ListaDistribucion.objects.filter(activa=True).count()
    
    # Mensajes recientes
    mensajes_recientes = Mensaje.objects.all().order_by('-fecha_creacion')[:5]
    
    # Notificaciones recientes
    notificaciones_recientes = Notificacion.objects.all().order_by('-fecha_creacion')[:5]
    
    # Estadísticas de envío del mes actual
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    
    envios_mes = SeguimientoEnvio.objects.filter(
        fecha_envio__gte=primer_dia_mes,
        fecha_envio__lte=hoy
    )
    
    total_envios_mes = envios_mes.count()
    envios_exitosos_mes = envios_mes.filter(estado='enviado').count()
    tasa_exito = (envios_exitosos_mes / total_envios_mes * 100) if total_envios_mes > 0 else 0
    
    # Notificaciones no leídas (simulando usuario actual)
    notificaciones_pendientes = Notificacion.objects.filter(
        leida=False
    ).count()
    
    context = {
        'total_mensajes': total_mensajes,
        'mensajes_enviados': mensajes_enviados,
        'mensajes_pendientes': mensajes_pendientes,
        'listas_distribucion': total_listas,
        'mensajes_recientes': mensajes_recientes,
        'notificaciones_recientes': notificaciones_recientes,
        'total_envios_mes': total_envios_mes,
        'envios_exitosos_mes': envios_exitosos_mes,
        'tasa_exito': round(tasa_exito, 1),
        'notificaciones_pendientes': notificaciones_pendientes,
    }
    
    return render(request, 'core/comunicaciones/dashboard_comunicaciones.html', context)

# ------------------------------------------------------------------
# Gestión de Listas de Distribución
# ------------------------------------------------------------------
def listar_listas_distribucion(request):
    """Lista todas las listas de distribución"""
    listas = ListaDistribucion.objects.all().order_by('-fecha_creacion')
    
    # Agregar conteo de miembros para cada lista
    for lista in listas:
        lista.total_miembros = lista.obtener_miembros().count()
    
    return render(request, 'core/comunicaciones/listar_listas_distribucion.html', {
        'listas': listas
    })

def crear_lista_distribucion(request):
    """Crear nueva lista de distribución"""
    if request.method == 'POST':
        form = ListaDistribucionForm(request.POST)
        if form.is_valid():
            try:
                lista = form.save(commit=False)
                lista.creado_por = 'Sistema'  # En producción usar request.user
                lista.save()
                
                # Guardar grupos seleccionados
                form.save_m2m()
                
                messages.success(request, f'Lista de distribución "{lista.nombre}" creada exitosamente.')
                return redirect('listar_listas_distribucion')
                
            except Exception as e:
                messages.error(request, f'Error al crear la lista: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ListaDistribucionForm()
    
    return render(request, 'core/comunicaciones/crear_lista_distribucion.html', {
        'form': form
    })

def detalle_lista_distribucion(request, lista_id):
    """Ver detalles de una lista de distribución"""
    lista = get_object_or_404(ListaDistribucion, pk=lista_id)
    miembros = lista.obtener_miembros()
    
    # Paginación
    paginator = Paginator(miembros, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'lista': lista,
        'miembros': page_obj,
        'total_miembros': miembros.count(),
    }
    
    return render(request, 'core/comunicaciones/detalle_lista_distribucion.html', context)

def editar_lista_distribucion(request, lista_id):
    """Editar lista de distribución"""
    lista = get_object_or_404(ListaDistribucion, pk=lista_id)
    
    if request.method == 'POST':
        lista.nombre = request.POST.get('nombre')
        lista.descripcion = request.POST.get('descripcion')
        lista.tipo = request.POST.get('tipo')
        lista.incluir_solo_activos = request.POST.get('incluir_solo_activos') == 'on'
        lista.incluir_solo_con_email = request.POST.get('incluir_solo_con_email') == 'on'
        lista.activa = request.POST.get('activa') == 'on'
        
        grupos_seleccionados = request.POST.getlist('grupos')
        
        try:
            lista.save()
            
            # Actualizar grupos
            if grupos_seleccionados:
                grupos = Grupo.objects.filter(id_grupo__in=grupos_seleccionados)
                lista.incluir_grupos.set(grupos)
            else:
                lista.incluir_grupos.clear()
            
            messages.success(request, 'Lista de distribución actualizada exitosamente.')
            return redirect('detalle_lista_distribucion', lista_id=lista.id_lista)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar la lista: {str(e)}')
    
    grupos = Grupo.objects.all().order_by('nombre_grupo')
    grupos_seleccionados = lista.incluir_grupos.all()
    
    return render(request, 'core/comunicaciones/editar_lista_distribucion.html', {
        'lista': lista,
        'grupos': grupos,
        'grupos_seleccionados': grupos_seleccionados
    })

# ------------------------------------------------------------------
# Gestión de Mensajes
# ------------------------------------------------------------------
def listar_mensajes(request):
    """Lista todos los mensajes"""
    mensajes = Mensaje.objects.all().order_by('-fecha_creacion')
    
    # Filtros
    estado_filtro = request.GET.get('estado', '')
    tipo_filtro = request.GET.get('tipo', '')
    busqueda = request.GET.get('busqueda', '')
    
    if estado_filtro:
        mensajes = mensajes.filter(estado=estado_filtro)
    
    if tipo_filtro:
        mensajes = mensajes.filter(tipo=tipo_filtro)
    
    if busqueda:
        mensajes = mensajes.filter(
            Q(titulo__icontains=busqueda) |
            Q(contenido__icontains=busqueda) |
            Q(asunto_email__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(mensajes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'mensajes': page_obj,
        'estado_filtro': estado_filtro,
        'tipo_filtro': tipo_filtro,
        'busqueda': busqueda,
    }
    
    return render(request, 'core/comunicaciones/listar_mensajes.html', context)

def crear_mensaje(request):
    """Crear nuevo mensaje"""
    if request.method == 'POST':
        form = MensajeForm(request.POST)
        if form.is_valid():
            try:
                mensaje = form.save(commit=False)
                mensaje.creado_por = 'Sistema'  # En producción usar request.user
                
                # Programar envío si se especifica fecha
                if form.cleaned_data.get('fecha_programada'):
                    mensaje.estado = 'programado'
                
                mensaje.save()
                
                # Guardar destinatarios personalizados
                form.save_m2m()
                
                # Calcular total de destinatarios
                total_destinatarios = len(mensaje.obtener_destinatarios())
                mensaje.total_destinatarios = total_destinatarios
                mensaje.save()
                
                messages.success(request, f'Mensaje "{mensaje.titulo}" creado exitosamente con {total_destinatarios} destinatarios.')
                return redirect('listar_mensajes')
                
            except Exception as e:
                messages.error(request, f'Error al crear el mensaje: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = MensajeForm()
    
    return render(request, 'core/comunicaciones/crear_mensaje.html', {
        'form': form
    })

def detalle_mensaje(request, mensaje_id):
    """Ver detalles de un mensaje"""
    mensaje = get_object_or_404(Mensaje, pk=mensaje_id)
    
    # Obtener seguimientos de envío
    seguimientos = SeguimientoEnvio.objects.filter(mensaje=mensaje).order_by('-fecha_envio')
    
    # Estadísticas de envío
    total_seguimientos = seguimientos.count()
    enviados = seguimientos.filter(estado='enviado').count()
    errores = seguimientos.filter(estado='error').count()
    pendientes = seguimientos.filter(estado='pendiente').count()
    
    # Paginación de seguimientos
    paginator = Paginator(seguimientos, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'mensaje': mensaje,
        'seguimientos': page_obj,
        'total_seguimientos': total_seguimientos,
        'enviados': enviados,
        'errores': errores,
        'pendientes': pendientes,
        'tasa_exito': (enviados / total_seguimientos * 100) if total_seguimientos > 0 else 0
    }
    
    return render(request, 'core/comunicaciones/detalle_mensaje.html', context)

def enviar_mensaje(request, mensaje_id):
    """Enviar mensaje inmediatamente con lógica real de email"""
    mensaje = get_object_or_404(Mensaje, pk=mensaje_id)
    
    if mensaje.estado not in ['borrador', 'programado']:
        messages.error(request, 'Este mensaje ya ha sido enviado o está en proceso.')
        return redirect('detalle_mensaje', mensaje_id=mensaje_id)
    
    try:
        # Cambiar estado a enviando
        mensaje.estado = 'enviando'
        mensaje.fecha_envio = timezone.now()
        mensaje.save()
        
        # Obtener configuración de comunicación
        try:
            config = ConfiguracionComunicacion.objects.first()
            if not config or not config.smtp_configurado:
                raise Exception("Configuración SMTP no encontrada o incompleta")
        except ConfiguracionComunicacion.DoesNotExist:
            raise Exception("Configuración de comunicación no encontrada")
        
        # Obtener destinatarios
        destinatarios = mensaje.obtener_destinatarios()
        
        # Configurar conexión SMTP
        if config.smtp_ssl:
            server = smtplib.SMTP_SSL(config.smtp_servidor, config.smtp_puerto)
        else:
            server = smtplib.SMTP(config.smtp_servidor, config.smtp_puerto)
            if config.smtp_tls:
                server.starttls()
        
        server.login(config.smtp_usuario, config.smtp_password)
        
        # Enviar emails
        enviados_exitosos = 0
        for destinatario in destinatarios:
            if destinatario.email:
                try:
                    # Crear seguimiento
                    seguimiento, created = SeguimientoEnvio.objects.get_or_create(
                        mensaje=mensaje,
                        destinatario=destinatario,
                        defaults={
                            'email_destinatario': destinatario.email,
                            'estado': 'pendiente'
                        }
                    )
                    
                    # Preparar email
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = mensaje.asunto_email or mensaje.titulo
                    msg['From'] = config.email_remitente
                    msg['To'] = destinatario.email
                    
                    # Contenido del email
                    if mensaje.tipo == 'email':
                        contenido = mensaje.contenido_email or mensaje.contenido
                    else:
                        contenido = mensaje.contenido
                    
                    # Personalizar contenido
                    contenido_personalizado = contenido.replace(
                        '{nombre}', f"{destinatario.nombre} {destinatario.apellido}"
                    )
                    
                    # Agregar partes del mensaje
                    part1 = MIMEText(contenido_personalizado, 'plain', 'utf-8')
                    part2 = MIMEText(contenido_personalizado, 'html', 'utf-8')
                    
                    msg.attach(part1)
                    msg.attach(part2)
                    
                    # Enviar
                    server.send_message(msg)
                    
                    # Actualizar seguimiento
                    seguimiento.estado = 'enviado'
                    seguimiento.fecha_envio = timezone.now()
                    seguimiento.save()
                    
                    enviados_exitosos += 1
                    
                except Exception as e:
                    # Error en envío individual
                    seguimiento.estado = 'error'
                    seguimiento.error_detalle = str(e)
                    seguimiento.save()
        
        server.quit()
        
        # Actualizar estadísticas del mensaje
        mensaje.estado = 'enviado'
        mensaje.total_enviados = enviados_exitosos
        mensaje.save()
        
        messages.success(request, f'Mensaje enviado exitosamente a {enviados_exitosos} destinatarios.')
        
    except Exception as e:
        mensaje.estado = 'error'
        mensaje.save()
        messages.error(request, f'Error al enviar el mensaje: {str(e)}')
    
    return redirect('detalle_mensaje', mensaje_id=mensaje_id)

# ------------------------------------------------------------------
# Gestión de Plantillas
# ------------------------------------------------------------------
def listar_plantillas_mensaje(request):
    """Lista todas las plantillas de mensaje"""
    plantillas = PlantillaMensaje.objects.all().order_by('-fecha_creacion')
    
    return render(request, 'core/comunicaciones/listar_plantillas_mensaje.html', {
        'plantillas': plantillas
    })

def crear_plantilla_mensaje(request):
    """Crear nueva plantilla de mensaje"""
    if request.method == 'POST':
        form = PlantillaMensajeForm(request.POST)
        if form.is_valid():
            try:
                plantilla = form.save(commit=False)
                plantilla.creado_por = 'Sistema'  # En producción usar request.user
                plantilla.save()
                
                messages.success(request, f'Plantilla "{plantilla.nombre}" creada exitosamente.')
                return redirect('listar_plantillas_mensaje')
                
            except Exception as e:
                messages.error(request, f'Error al crear la plantilla: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = PlantillaMensajeForm()
    
    return render(request, 'core/comunicaciones/crear_plantilla_mensaje.html', {
        'form': form
    })

def editar_plantilla_mensaje(request, plantilla_id):
    """Editar plantilla de mensaje existente"""
    try:
        plantilla = PlantillaMensaje.objects.get(pk=plantilla_id)
    except PlantillaMensaje.DoesNotExist:
        messages.error(request, 'Plantilla no encontrada.')
        return redirect('listar_plantillas_mensaje')
    
    if request.method == 'POST':
        form = PlantillaMensajeForm(request.POST, instance=plantilla)
        if form.is_valid():
            try:
                plantilla = form.save()
                messages.success(request, f'Plantilla "{plantilla.nombre}" actualizada exitosamente.')
                return redirect('listar_plantillas_mensaje')
            except Exception as e:
                messages.error(request, f'Error al actualizar la plantilla: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = PlantillaMensajeForm(instance=plantilla)
    
    return render(request, 'core/comunicaciones/editar_plantilla_mensaje.html', {
        'form': form,
        'plantilla': plantilla
    })

def eliminar_plantilla_mensaje(request, plantilla_id):
    """Eliminar plantilla de mensaje"""
    try:
        plantilla = PlantillaMensaje.objects.get(pk=plantilla_id)
    except PlantillaMensaje.DoesNotExist:
        messages.error(request, 'Plantilla no encontrada.')
        return redirect('listar_plantillas_mensaje')
    
    if request.method == 'POST':
        nombre_plantilla = plantilla.nombre
        plantilla.delete()
        messages.success(request, f'Plantilla "{nombre_plantilla}" eliminada exitosamente.')
        return redirect('listar_plantillas_mensaje')
    
    return render(request, 'core/comunicaciones/eliminar_plantilla_mensaje.html', {
        'plantilla': plantilla
    })

# ------------------------------------------------------------------
# Gestión de Notificaciones
# ------------------------------------------------------------------
def listar_notificaciones(request):
    """Lista todas las notificaciones"""
    notificaciones = Notificacion.objects.all().order_by('-fecha_creacion')
    
    # Filtros
    tipo_filtro = request.GET.get('tipo', '')
    estado_filtro = request.GET.get('estado', '')
    
    if tipo_filtro:
        notificaciones = notificaciones.filter(tipo=tipo_filtro)
    
    if estado_filtro == 'leidas':
        notificaciones = notificaciones.filter(leida=True)
    elif estado_filtro == 'no_leidas':
        notificaciones = notificaciones.filter(leida=False)
    
    # Paginación
    paginator = Paginator(notificaciones, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notificaciones': page_obj,
        'tipo_filtro': tipo_filtro,
        'estado_filtro': estado_filtro,
    }
    
    return render(request, 'core/comunicaciones/listar_notificaciones.html', context)

def crear_notificacion(request):
    """Crear nueva notificación"""
    if request.method == 'POST':
        form = NotificacionForm(request.POST)
        if form.is_valid():
            try:
                notificacion = form.save(commit=False)
                notificacion.creado_por = 'Sistema'  # En producción usar request.user
                notificacion.save()
                
                messages.success(request, f'Notificación creada para {notificacion.destinatario.nombre} {notificacion.destinatario.apellido}.')
                return redirect('listar_notificaciones')
                
            except Exception as e:
                messages.error(request, f'Error al crear la notificación: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = NotificacionForm()
    
    # Configurar queryset para destinatarios
    form.fields['destinatario'].queryset = Miembro.objects.filter(estado='Activo').order_by('nombre', 'apellido')
    
    return render(request, 'core/comunicaciones/crear_notificacion.html', {
        'form': form
    })

def marcar_notificacion_leida(request, notificacion_id):
    """Marcar notificación como leída"""
    if request.method == 'POST':
        try:
            notificacion = Notificacion.objects.get(pk=notificacion_id)
            notificacion.marcar_como_leida()
            return JsonResponse({'success': True})
        except Notificacion.DoesNotExist:
            return JsonResponse({'error': 'Notificación no encontrada'}, status=404)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def eliminar_notificacion(request, notificacion_id):
    """Eliminar notificación"""
    if request.method == 'POST':
        try:
            notificacion = Notificacion.objects.get(pk=notificacion_id)
            titulo = notificacion.titulo
            notificacion.delete()
            return JsonResponse({'success': True, 'message': f'Notificación "{titulo}" eliminada'})
        except Notificacion.DoesNotExist:
            return JsonResponse({'error': 'Notificación no encontrada'}, status=404)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

# ------------------------------------------------------------------
# Configuración del Sistema
# ------------------------------------------------------------------
def configuracion_comunicacion(request):
    """Configuración del sistema de comunicación"""
    try:
        config = ConfiguracionComunicacion.objects.first()
        if not config:
            config = ConfiguracionComunicacion.objects.create()
    except:
        config = ConfiguracionComunicacion.objects.create()
    
    if request.method == 'POST':
        form = ConfiguracionComunicacionForm(request.POST, instance=config)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Configuración guardada exitosamente.')
                return redirect('configuracion_comunicacion')
            except Exception as e:
                messages.error(request, f'Error al guardar la configuración: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ConfiguracionComunicacionForm(instance=config)
    
    return render(request, 'core/comunicaciones/configuracion_comunicacion.html', {
        'form': form,
        'config': config
    })

# ------------------------------------------------------------------
# API para AJAX
# ------------------------------------------------------------------
def api_preview_lista_distribucion(request, lista_id):
    """API para previsualizar miembros de una lista de distribución"""
    try:
        lista = ListaDistribucion.objects.get(pk=lista_id)
        miembros = lista.obtener_miembros()[:10]  # Solo los primeros 10 para preview
        
        data = {
            'total': lista.obtener_miembros().count(),
            'miembros': [
                {
                    'nombre': f"{m.nombre} {m.apellido}",
                    'email': m.email
                } for m in miembros
            ]
        }
        
        return JsonResponse(data)
    except ListaDistribucion.DoesNotExist:
        return JsonResponse({'error': 'Lista no encontrada'}, status=404)

def api_plantilla_mensaje(request, plantilla_id):
    """API para obtener contenido de una plantilla"""
    try:
        plantilla = PlantillaMensaje.objects.get(pk=plantilla_id)
        
        data = {
            'asunto': plantilla.asunto,
            'contenido_html': plantilla.contenido_html,
            'contenido_texto': plantilla.contenido_texto,
            'variables': plantilla.variables_disponibles
        }
        
        return JsonResponse(data)
    except PlantillaMensaje.DoesNotExist:
        return JsonResponse({'error': 'Plantilla no encontrada'}, status=404)

# NUEVAS VISTAS NECESARIAS
def reporte_promesas(request):
    """Reporte de promesas activas, cumplidas y vencidas"""
    pass

def reporte_proyectos(request):
    """Progreso de proyectos financieros"""
    pass

def reporte_presupuesto_vs_real(request):
    """Comparación presupuesto vs ejecución real"""
    pass

def reporte_diezmos_familiares(request):
    """Seguimiento de diezmos por familia"""
    pass

def dashboard_proyectos(request):
    """Dashboard específico para proyectos"""
    pass