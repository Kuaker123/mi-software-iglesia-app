from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Miembro, Contribucion, Grupo
from decimal import Decimal

User = get_user_model()

class MiembroViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            rol='admin'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.miembro = Miembro.objects.create(
            nombre='Juan',
            apellido='Pérez',
            genero='M',
            estado='Activo'
        )
    
    def test_listar_miembros(self):
        """Test vista listar miembros"""
        response = self.client.get(reverse('listar_miembros'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Juan Pérez')
    
    def test_crear_miembro_get(self):
        """Test GET crear miembro"""
        response = self.client.get(reverse('crear_miembro'))
        self.assertEqual(response.status_code, 200)
    
    def test_crear_miembro_post(self):
        """Test POST crear miembro"""
        data = {
            'nombre': 'María',
            'apellido': 'González',
            'genero': 'F',
            'estado': 'Activo',
            'email': 'maria@example.com'
        }
        response = self.client.post(reverse('crear_miembro'), data)
        self.assertEqual(response.status_code, 302)  # Redirect después de crear
        self.assertTrue(Miembro.objects.filter(nombre='María').exists())
    
    def test_detalle_miembro(self):
        """Test vista detalle miembro"""
        response = self.client.get(reverse('detalle_miembro', args=[self.miembro.id_miembro]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Juan Pérez')

class ContribucionViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            rol='editor'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.miembro = Miembro.objects.create(
            nombre='Juan',
            apellido='Pérez',
            genero='M',
            estado='Activo'
        )
    
    def test_listar_contribuciones(self):
        """Test vista listar contribuciones"""
        Contribucion.objects.create(
            id_miembro=self.miembro,
            cantidad=Decimal('100.00'),
            categoria='Diezmo'
        )
        
        response = self.client.get(reverse('listar_contribuciones'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '100.00')
    
    def test_crear_contribucion_post(self):
        """Test POST crear contribución"""
        data = {
            'id_miembro': self.miembro.id_miembro,
            'cantidad': '150.00',
            'tipo_contribucion': 'Ingreso',
            'categoria': 'Ofrenda',
            'metodo_pago': 'Efectivo'
        }
        response = self.client.post(reverse('crear_contribucion'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Contribucion.objects.filter(cantidad=Decimal('150.00')).exists())