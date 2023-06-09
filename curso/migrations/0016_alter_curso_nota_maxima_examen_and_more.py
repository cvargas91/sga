# Generated by Django 4.0.3 on 2022-10-21 14:54

import curso.validadores
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curso', '0015_alter_curso_nota_maxima_examen_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='curso',
            name='nota_maxima_examen',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True, validators=[curso.validadores.validatar_nota]),
        ),
        migrations.AlterField(
            model_name='curso',
            name='nota_minima_examen',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True, validators=[curso.validadores.validatar_nota]),
        ),
    ]
