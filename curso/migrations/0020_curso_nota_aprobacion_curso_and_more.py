# Generated by Django 4.0.3 on 2022-10-27 21:07

import curso.validadores
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curso', '0019_alter_categoriaactividad_plan_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='nota_aprobacion_curso',
            field=models.DecimalField(decimal_places=2, default=4, max_digits=3, validators=[curso.validadores.validatar_nota]),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='estudiantecurso',
            name='nota_examen',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='estudiantecurso',
            name='nota_final',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True),
        ),
        migrations.AlterField(
            model_name='estudiantecurso',
            name='nota_presentacion',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=3, null=True),
        ),
    ]
