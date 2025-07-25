# Generated by Django 5.2.4 on 2025-07-19 07:36

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_usuario_date_joined_alter_usuario_groups_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='evento',
            options={'ordering': ['-fecha_evento'], 'verbose_name': 'Evento', 'verbose_name_plural': 'Eventos'},
        ),
        migrations.RenameField(
            model_name='tipocertificado',
            old_name='requiere_fecha_evento',
            new_name='requiere_evento',
        ),
        migrations.RemoveField(
            model_name='evento',
            name='id_grupo_responsable',
        ),
        migrations.RemoveField(
            model_name='evento',
            name='publico',
        ),
        migrations.RemoveField(
            model_name='grupo',
            name='id_lider',
        ),
        migrations.RemoveField(
            model_name='grupo',
            name='ubicacion_geografica',
        ),
        migrations.RemoveField(
            model_name='tipocertificado',
            name='plantilla_html',
        ),
        migrations.RemoveField(
            model_name='tipocertificado',
            name='requiere_pastor',
        ),
        migrations.AddField(
            model_name='evento',
            name='capacidad_maxima',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='evento',
            name='costo',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='evento',
            name='estado',
            field=models.CharField(choices=[('programado', 'Programado'), ('en_curso', 'En Curso'), ('finalizado', 'Finalizado'), ('cancelado', 'Cancelado')], default='programado', max_length=20),
        ),
        migrations.AddField(
            model_name='grupo',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='grupo',
            name='lider',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='grupos_liderados', to='core.miembro'),
        ),
        migrations.AddField(
            model_name='tipocertificado',
            name='plantilla_contenido',
            field=models.TextField(default='Certificado de {tipo}\n\nPor medio del presente certificamos que:\n\n{nombre_completo}\n\nHa cumplido con los requisitos establecidos.\n\nFecha: {fecha}\nPastor: {pastor}', help_text='Plantilla del contenido del certificado'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='evento',
            name='nombre_evento',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='evento',
            name='ubicacion',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='miembro',
            name='apellido',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='miembro',
            name='direccion',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='miembro',
            name='email',
            field=models.EmailField(blank=True, db_index=True, max_length=100, null=True, unique=True, validators=[django.core.validators.EmailValidator()]),
        ),
        migrations.AlterField(
            model_name='miembro',
            name='estado',
            field=models.CharField(choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo'), ('Pendiente', 'Pendiente')], db_index=True, default='Activo', max_length=20),
        ),
        migrations.AlterField(
            model_name='miembro',
            name='fecha_ingreso',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='miembro',
            name='genero',
            field=models.CharField(choices=[('M', 'Masculino'), ('F', 'Femenino')], default='no_especificado', max_length=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='miembro',
            name='nombre',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AddIndex(
            model_name='certificado',
            index=models.Index(fields=['fecha_emision', 'estado'], name='certificado_fecha_e_f9e9ef_idx'),
        ),
        migrations.AddIndex(
            model_name='certificado',
            index=models.Index(fields=['id_miembro', 'tipo_certificado'], name='certificado_id_miem_86651c_idx'),
        ),
        migrations.AddIndex(
            model_name='contribucion',
            index=models.Index(fields=['fecha_contribucion', 'tipo_contribucion'], name='contribucio_fecha_c_6b3723_idx'),
        ),
        migrations.AddIndex(
            model_name='contribucion',
            index=models.Index(fields=['id_miembro', 'fecha_contribucion'], name='contribucio_id_miem_56f786_idx'),
        ),
        migrations.AddIndex(
            model_name='miembro',
            index=models.Index(fields=['estado', 'fecha_ingreso'], name='miembros_estado_dea671_idx'),
        ),
        migrations.AddIndex(
            model_name='miembro',
            index=models.Index(fields=['nombre', 'apellido'], name='miembros_nombre_490f98_idx'),
        ),
        migrations.AddIndex(
            model_name='miembro',
            index=models.Index(fields=['email'], name='miembros_email_989231_idx'),
        ),
        migrations.AddIndex(
            model_name='miembro',
            index=models.Index(fields=['fecha_nacimiento'], name='miembros_fecha_n_440df5_idx'),
        ),
        migrations.AlterModelTable(
            name='certificado',
            table='certificados',
        ),
        migrations.AlterModelTable(
            name='contribucion',
            table='contribuciones',
        ),
        migrations.AlterModelTable(
            name='evento',
            table='eventos',
        ),
        migrations.AlterModelTable(
            name='grupo',
            table='grupos',
        ),
        migrations.AlterModelTable(
            name='miembro',
            table='miembros',
        ),
        migrations.AlterModelTable(
            name='tipocertificado',
            table='tipos_certificados',
        ),
    ]
