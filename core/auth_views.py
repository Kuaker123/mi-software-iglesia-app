from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import IntegrityError
from .models import Usuario, Miembro
from .auth_decorators import admin_required, role_based_redirect
from django.contrib.auth.forms import UserCreationForm
from django import forms

class UsuarioCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)
    
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'iglesia')
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'rol': 'Rol',
            'iglesia': 'Iglesia'
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

def login_view(request):
    if request.user.is_authenticated:
        return redirect(role_based_redirect(request.user))
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None and user.activo:
            login(request, user)
            # Actualizar último acceso
            user.fecha_ultimo_acceso = timezone.now()
            user.save()
            
            messages.success(request, f'¡Bienvenido {user.first_name}!')
            return redirect(role_based_redirect(user))
        else:
            messages.error(request, 'Credenciales inválidas o usuario inactivo.')
    
    return render(request, 'auth/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('login')

@admin_required
def gestionar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('-date_joined')
    return render(request, 'auth/gestionar_usuarios.html', {'usuarios': usuarios})

@admin_required
def crear_usuario(request):
    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            try:
                usuario = form.save()
                usuario.creado_por = request.user
                usuario.save()
                messages.success(request, f'Usuario {usuario.username} creado exitosamente.')
                return redirect('gestionar_usuarios')
            except IntegrityError:
                messages.error(request, 'El nombre de usuario ya existe.')
    else:
        form = UsuarioCreationForm()
    
    return render(request, 'auth/crear_usuario.html', {'form': form})

@admin_required
def toggle_usuario_estado(request, user_id):
    usuario = get_object_or_404(Usuario, id=user_id)
    usuario.activo = not usuario.activo
    usuario.save()
    
    estado = "activado" if usuario.activo else "desactivado"
    messages.success(request, f'Usuario {usuario.username} {estado} exitosamente.')
    return redirect('gestionar_usuarios')

@login_required
def dashboard_view(request):
    """Vista principal del dashboard que redirige según el rol"""
    return redirect(role_based_redirect(request.user))

@login_required
def admin_dashboard(request):
    """Dashboard específico para administradores"""
    if request.user.rol != 'admin':
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    context = {
        'total_usuarios': Usuario.objects.count(),
        'usuarios_activos': Usuario.objects.filter(activo=True).count(),
        'total_miembros': Miembro.objects.count(),
    }
    return render(request, 'dashboards/admin_dashboard.html', context)

@login_required
def editor_dashboard(request):
    """Dashboard específico para editores"""
    if request.user.rol not in ['editor', 'admin']:
        messages.error(request, 'Acceso denegado.')
        return redirect('dashboard')
    
    context = {
        'total_miembros': Miembro.objects.count(),
        'miembros_activos': Miembro.objects.filter(estado='Activo').count(),
    }
    return render(request, 'dashboards/editor_dashboard.html', context)

@login_required
def observador_dashboard(request):
    """Dashboard específico para observadores"""
    context = {
        'total_miembros': Miembro.objects.filter(estado='Activo').count(),
    }
    return render(request, 'dashboards/observador_dashboard.html', context)