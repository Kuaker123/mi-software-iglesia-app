from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from core.admin import custom_admin_site

urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('core/', include('core.urls')),  # Ya está correcto
    path('', lambda request: redirect('/core/')),  # Cambio menor aquí
]
