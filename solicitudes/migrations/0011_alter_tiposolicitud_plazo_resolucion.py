# Generated by Django 4.0.3 on 2022-05-30 19:44

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('solicitudes', '0010_auto_20220421_1711'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tiposolicitud',
            name='plazo_resolucion',
            field=models.DurationField(default=datetime.timedelta(days=84)),
        ),
    ]