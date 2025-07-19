from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, timedelta
from decimal import Decimal
from core.models import Miembro, Contribucion, Grupo, Evento, Certificado, TipoCertificado
from django.utils import timezone

class MiembroModelTest(TestCase):
    def setUp(self):
        self.miembro_data = {
            'nombre': 'Juan',
            'apellido': 'Pérez',
            'fecha_nacimiento': date(1990, 1, 1),
            'genero': 'M',
            'email': 'juan@example.com',
            'telefono': '1234567890',
            'estado': 'Activo'
        }
    
    def test_crear_miembro_valido(self):
        """Test crear miembro con datos válidos"""
        miembro = Miembro.objects.create(**self.miembro_data)
        self.assertEqual(miembro.nombre, 'Juan')
        self.assertEqual(miembro.apellido, 'Pérez')
        self.assertTrue(miembro.activo)
        self.assertEqual(str(miembro), 'Juan Pérez')
    
    def test_calcular_edad(self):
        """Test cálculo de edad"""
        miembro = Miembro.objects.create(**self.miembro_data)
        edad_esperada = date.today().year - 1990
        if date.today() < date(date.today().year, 1, 1):
            edad_esperada -= 1
        self.assertEqual(miembro.calcular_edad(), edad_esperada)
    
    def test_email_unico(self):
        """Test que el email sea único"""
        Miembro.objects.create(**self.miembro_data)
        
        # Intentar crear otro miembro con el mismo email
        miembro_data_2 = self.miembro_data.copy()
        miembro_data_2['nombre'] = 'María'
        
        miembro2 = Miembro(**miembro_data_2)
        with self.assertRaises(ValidationError):
            miembro2.full_clean()
    
    def test_fecha_nacimiento_futura(self):
        """Test validación fecha de nacimiento futura"""
        self.miembro_data['fecha_nacimiento'] = date.today() + timedelta(days=1)
        miembro = Miembro(**self.miembro_data)
        
        with self.assertRaises(ValidationError):
            miembro.full_clean()
    
    def test_nombre_completo_property(self):
        """Test propiedad nombre_completo"""
        miembro = Miembro.objects.create(**self.miembro_data)
        self.assertEqual(miembro.nombre_completo, 'Juan Pérez')

class ContribucionModelTest(TestCase):
    def setUp(self):
        self.miembro = Miembro.objects.create(
            nombre='Juan',
            apellido='Pérez',
            genero='M',
            estado='Activo'
        )
        
        self.contribucion_data = {
            'id_miembro': self.miembro,
            'cantidad': Decimal('100.00'),
            'tipo_contribucion': 'Ingreso',
            'categoria': 'Diezmo',
            'metodo_pago': 'Efectivo'
        }
    
    def test_crear_contribucion_valida(self):
        """Test crear contribución válida"""
        contribucion = Contribucion.objects.create(**self.contribucion_data)
        self.assertEqual(contribucion.cantidad, Decimal('100.00'))
        self.assertEqual(contribucion.categoria, 'Diezmo')
        self.assertEqual(str(contribucion), 'Juan Pérez - $100.00 (Diezmo)')
    
    def test_cantidad_negativa(self):
        """Test validación cantidad negativa"""
        self.contribucion_data['cantidad'] = Decimal('-50.00')
        contribucion = Contribucion(**self.contribucion_data)
        
        with self.assertRaises(ValidationError):
            contribucion.full_clean()
    
    def test_cantidad_cero(self):
        """Test validación cantidad cero"""
        self.contribucion_data['cantidad'] = Decimal('0.00')
        contribucion = Contribucion(**self.contribucion_data)
        
        with self.assertRaises(ValidationError):
            contribucion.full_clean()
    
    def test_fecha_futura(self):
        """Test validación fecha futura"""
        self.contribucion_data['fecha_contribucion'] = timezone.now() + timedelta(days=1)
        contribucion = Contribucion(**self.contribucion_data)
        
        with self.assertRaises(ValidationError):
            contribucion.full_clean()

class GrupoModelTest(TestCase):
    def setUp(self):
        self.lider = Miembro.objects.create(
            nombre='Pedro',
            apellido='García',
            genero='M',
            estado='Activo'
        )
    
    def test_crear_grupo(self):
        """Test crear grupo"""
        grupo = Grupo.objects.create(
            nombre_grupo='Jóvenes',
            descripcion='Grupo de jóvenes',
            id_lider=self.lider
        )
        self.assertEqual(grupo.nombre_grupo, 'Jóvenes')
        self.assertEqual(grupo.id_lider, self.lider)
        self.assertEqual(str(grupo), 'Jóvenes')