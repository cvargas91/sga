# Generated by Django 4.0.3 on 2022-11-21 19:05

import curso.validadores
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curso', '0024_alter_actividad_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='curso',
            name='nota_aprobacion_curso',
            field=models.DecimalField(decimal_places=2, default=4, max_digits=3, validators=[curso.validadores.validatar_nota]),
        ),
    ]