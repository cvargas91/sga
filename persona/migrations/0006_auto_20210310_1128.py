# Generated by Django 3.1.2 on 2021-03-10 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('persona', '0005_auto_20210228_0215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='estudiante',
            name='estado',
            field=models.PositiveSmallIntegerField(choices=[(0, 'regular'), (1, 'congelado'), (2, 'abandono'), (3, 'eliminado'), (4, 'suspendido'), (5, 'completado'), (6, 'matrícula pendiente'), (7, 'matrícula anulada por cambio de carrera'), (8, 'matrícula anulada por retracto'), (9, 'matrícula anulada por otro motivo')], default=0),
        ),
    ]