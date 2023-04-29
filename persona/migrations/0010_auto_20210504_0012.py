# Generated by Django 3.1.2 on 2021-05-04 04:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('persona', '0009_auto_20210316_1238'),
    ]

    operations = [
        migrations.AddField(
            model_name='persona',
            name='educontinua_cargo',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='persona',
            name='educontinua_empresa',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='persona',
            name='educontinua_mail_laboral',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='estudiante',
            name='estado',
            field=models.PositiveSmallIntegerField(choices=[(0, 'regular'), (1, 'congelado'), (2, 'abandono'), (3, 'eliminado'), (4, 'suspendido'), (5, 'completado'), (6, 'matrícula pendiente'), (7, 'matrícula anulada por cambio de carrera'), (8, 'matrícula anulada por retracto'), (9, 'matrícula anulada por otro motivo'), (10, 'No Activo'), (11, 'retiro voluntario'), (12, 'no regular')], default=0),
        ),
    ]