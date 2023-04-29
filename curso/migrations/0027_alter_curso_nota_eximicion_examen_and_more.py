# Generated by Django 4.0.3 on 2022-11-30 02:10

import curso.validadores
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curso', '0026_merge_20221123_1654'),
    ]

    operations = [
        migrations.AlterField(
            model_name='curso',
            name='nota_eximicion_examen',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=3, null=True, validators=[curso.validadores.validatar_nota]),
        ),
        migrations.AlterField(
            model_name='curso',
            name='nota_minima_examen',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=3, null=True, validators=[curso.validadores.validatar_nota]),
        ),
    ]