from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied

def require_role(allowed_roles):
    """
    Decorador que requiere que el usuario tenga uno de los roles especificados
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if hasattr(request.user, 'rol') and request.user.rol in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'No tienes permisos para acceder a esta sección.')
                return redirect('dashboard')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """
    Decorador que requiere rol de administrador
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'rol') and request.user.rol == 'admin':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Solo los administradores pueden acceder a esta función.')
            return redirect('dashboard')
    return _wrapped_view

def editor_required(view_func):
    """
    Decorador que requiere rol de editor o superior
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'rol') and request.user.rol in ['editor', 'admin']:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'Necesitas permisos de editor para realizar esta acción.')
            return redirect('dashboard')
    return _wrapped_view

def observador_allowed(view_func):
    """
    Decorador para vistas que permiten todos los roles (solo requiere login)
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def role_based_redirect(user):
    """
    Función auxiliar para redirección inteligente basada en rol
    """
    if not hasattr(user, 'rol'):
        return '/core/'  # Redirigir al dashboard principal si no tiene rol

    if user.rol == 'admin':
        return '/admin-dashboard/'
    elif user.rol == 'editor':
        return '/editor-dashboard/'
    else:  # Rol 'observador' o cualquier otro rol no admin/editor
        return '/core/'  # Redirigir al dashboard principal
