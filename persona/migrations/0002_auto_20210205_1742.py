# Generated by Django 3.1.2 on 2021-02-05 20:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('persona', '0002_delete_matricula'), ('persona', '0003_persona_nombre_social'), ('persona', '0004_auto_20210203_2036'), ('persona', '0005_auto_20210204_0032'), ('persona', '0006_auto_20210205_0227'), ('persona', '0007_auto_20210205_0231'), ('persona', '0008_auto_20210205_1742')]

    dependencies = [
        ('general', '0001_initial'),
        ('persona', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Matricula',
        ),
        migrations.AddField(
            model_name='persona',
            name='nombre_social',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='persona',
            name='emergencia_nombre',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='persona',
            name='emergencia_parentezco',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='persona',
            name='emergencia_telefono_fijo',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='persona',
            name='emergencia_telefono_laboral',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='persona',
            name='direccion_comuna',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='general.comuna'),
        ),
        migrations.AddField(
            model_name='persona',
            name='genero',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='persona',
            name='emergencia_telefono_celular',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='persona',
            name='direccion_calle',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.RenameField(
            model_name='persona',
            old_name='nombre1',
            new_name='nombres',
        ),
        migrations.RenameField(
            model_name='persona',
            old_name='rut',
            new_name='numero_documento',
        ),
        migrations.RemoveField(
            model_name='persona',
            name='nombre2',
        ),
        migrations.AddField(
            model_name='persona',
            name='digito_verificador',
            field=models.CharField(blank=True, max_length=1, null=True),
        ),
        migrations.AddField(
            model_name='persona',
            name='direccion_block',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='persona',
            name='direccion_depto',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='persona',
            name='direccion_numero',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='persona',
            name='direccion_villa',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='persona',
            name='tipo_identificacion',
            field=models.PositiveSmallIntegerField(choices=[(0, 'cedula de identidad'), (1, 'pasaporte')], default=0),
        ),
        migrations.AlterField(
            model_name='estudiante',
            name='estado',
            field=models.PositiveSmallIntegerField(choices=[(0, 'regular'), (1, 'congelado'), (2, 'abandono'), (3, 'eliminado'), (4, 'suspendido'), (5, 'completado'), (6, 'matrícula pendiente')], default=0),
        ),
    ]