# Generated by Django 4.0 on 2021-12-30 17:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solicitudes', '0003_delete_estadoestudiante_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitud',
            name='estado',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Pendiente'), (1, 'Aprobada'), (2, 'Rechazada'), (3, 'No Procede'), (4, 'Expirada')]),
        ),
    ]
