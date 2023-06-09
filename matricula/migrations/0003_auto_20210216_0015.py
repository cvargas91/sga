# Generated by Django 3.1.2 on 2021-02-16 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academica', '0001_initial'),
        ('persona', '0003_auto_20210216_0049'),
        ('matricula', '0002_auto_20210211_1700'),
    ]

    operations = [
        migrations.RenameField(
            model_name='postulantedefinitivo',
            old_name='posicion_lista_espera',
            new_name='posicion_lista',
        ),
        migrations.AlterField(
            model_name='periodoprocesomatricula',
            name='fecha_fin',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='periodoprocesomatricula',
            name='fecha_inicio',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='postulantedefinitivo',
            name='acepta_vacante',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='postulantedefinitivo',
            name='preseleccionado_gratuidad',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterUniqueTogether(
            name='postulantedefinitivo',
            unique_together={('persona', 'proceso_matricula', 'plan')},
        ),
    ]
