# Generated by Django 4.0.4 on 2022-06-06 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solicitudes', '0015_solicitud_valida_causas'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitud',
            name='causas_revisor',
            field=models.ManyToManyField(blank=True, related_name='causas_revisor', to='solicitudes.causasolicitud'),
        ),
    ]
