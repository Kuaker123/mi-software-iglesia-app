from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

def require_role(roles_permitidos):
    """
    Decorador que requiere que el usuario tenga uno de los roles especificados
    
    Uso:
    @require_role(['editor', 'admin'])
    def mi_vista(request):
        pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not hasattr(request.user, 'rol'):
                messages.error(request, 'Tu usuario no tiene un rol asignado. Contacta al administrador.')
                return redirect('dashboard')
            
            if request.user.rol not in roles_permitidos:
                messages.error(request, f'No tienes permisos para acceder a esta sección. Rol requerido: {", ".join(roles_permitidos)}')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """
    Decorador que requiere rol de administrador
    """
    return require_role(['admin'])(view_func)

def editor_required(view_func):
    """
    Decorador que requiere rol de editor o admin
    """
    return require_role(['editor', 'admin'])(view_func)

def observador_allowed(view_func):
    """
    Decorador para vistas que todos los roles pueden ver
    """
    return require_role(['observador', 'editor', 'admin'])(view_func)