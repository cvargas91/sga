# Generated by Django 3.1.2 on 2020-12-11 18:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academica', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('curso', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Estudiante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.PositiveSmallIntegerField(choices=[(0, 'regular'), (1, 'congelado'), (2, 'abandono'), (3, 'eliminado'), (4, 'suspendido'), (5, 'completado')], default=0)),
                ('periodo_egreso', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='curso.periodo')),
                ('periodo_ingreso', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='curso.periodo')),
            ],
            options={
                'db_table': 'estudiante',
            },
        ),
        migrations.CreateModel(
            name='Persona',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rut', models.CharField(max_length=50, unique=True)),
                ('nombre1', models.CharField(max_length=100)),
                ('nombre2', models.CharField(blank=True, max_length=100)),
                ('apellido1', models.CharField(blank=True, max_length=100)),
                ('apellido2', models.CharField(blank=True, max_length=100)),
                ('foto', models.ImageField(blank=True, max_length=200, null=True, upload_to='fotos_perfil')),
                ('fecha_nacimiento', models.DateField(blank=True, null=True)),
                ('biografia', models.CharField(blank=True, max_length=300)),
                ('mail_secundario', models.EmailField(blank=True, max_length=200)),
                ('telefono_fijo', models.CharField(blank=True, max_length=20)),
                ('telefono_celular', models.CharField(blank=True, max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='persona', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'persona',
            },
        ),
        migrations.CreateModel(
            name='Matricula',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_documento', models.IntegerField()),
                ('numero_comprobante', models.IntegerField()),
                ('fecha', models.DateField()),
                ('estudiante', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='persona.estudiante')),
                ('periodo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='curso.periodo')),
            ],
            options={
                'db_table': 'matricula',
            },
        ),
        migrations.AddField(
            model_name='estudiante',
            name='persona',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='estudiantes', to='persona.persona'),
        ),
        migrations.AddField(
            model_name='estudiante',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='estudiantes', to='academica.plan'),
        ),
    ]