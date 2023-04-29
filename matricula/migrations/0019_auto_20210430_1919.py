# Generated by Django 3.1.2 on 2021-04-30 23:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matricula', '0018_auto_20210429_1322'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='arancelestudiante',
            name='descripcion',
        ),
        migrations.AddField(
            model_name='arancelestudiante',
            name='descripcion_beneficio',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='matriculaestudiante',
            name='beneficios_monto_total',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='matriculaestudiante',
            name='descripcion_beneficios',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='matriculaestudiante',
            name='monto_final',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='matriculaestudiante',
            name='tiene_beneficios',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='postulantepostgrado',
            name='descripcion_descuento_arancel',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='postulantepostgrado',
            name='descripcion_descuento_matricula',
            field=models.TextField(blank=True),
        ),
    ]
