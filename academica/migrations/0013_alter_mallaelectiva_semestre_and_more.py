# Generated by Django 4.0.3 on 2022-09-08 04:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academica', '0012_alter_carrera_tipo_carrera'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mallaelectiva',
            name='semestre',
            field=models.PositiveSmallIntegerField(help_text='semestre en el cuál se debe tomar este ramo/electivo'),
        ),
        migrations.AlterField(
            model_name='mallaobligatoria',
            name='semestre',
            field=models.PositiveSmallIntegerField(help_text='semestre en el cuál se debe tomar este ramo/electivo'),
        ),
        migrations.AlterField(
            model_name='plan',
            name='link_decreto',
            field=models.CharField(blank=True, help_text='\n            (solo para matrícula educación continua) ID del documento en google drive para generar\n            link al decreto en matrícula.<br>\n            Para obtenerlo se debe abrir el documento en una ventana nueva y en la url se encuentra\n            el id.<br>\n            e.g: en <a>https://drive.google.com/file/d/107vKi5LWk1fH2CwRLO_O-aC7SKBhkU84/view</a>\n            el id es <b>107vKi5LWk1fH2CwRLO_O-aC7SKBhkU84</b>.\n        ', max_length=300),
        ),
        migrations.AlterField(
            model_name='requisito',
            name='ramo',
            field=models.ForeignKey(help_text='ramo que tiene el requisito', on_delete=django.db.models.deletion.CASCADE, to='academica.ramo'),
        ),
    ]
