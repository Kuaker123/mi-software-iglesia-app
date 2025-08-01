# Generated by Django 4.2.16 on 2025-07-18 17:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20250718_0932'),
    ]

    operations = [
        # Paso 2: Agregar relaciones y restricciones únicas
        migrations.AddField(
            model_name='usuario',
            name='id_miembro',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuario_asociado', to='core.miembro'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        # Agregar restricción única para username
        migrations.AlterField(
            model_name='usuario',
            name='username',
            field=models.CharField(max_length=150, unique=True, verbose_name='username'),
        ),
    ]
