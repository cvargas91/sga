# Generated by Django 3.1.2 on 2021-03-16 15:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('matricula', '0013_auto_20210316_1238'),
        ('persona', '0008_persona_mail_institucional'),
    ]

    operations = [
        migrations.AddField(
            model_name='estudiante',
            name='via_ingreso',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='matricula.viaingreso'),
        ),
        migrations.AlterField(
            model_name='estudiante',
            name='estado',
            field=models.PositiveSmallIntegerField(choices=[(0, 'regular'), (1, 'congelado'), (2, 'abandono'), (3, 'eliminado'), (4, 'suspendido'), (5, 'completado'), (6, 'matrícula pendiente'), (7, 'matrícula anulada por cambio de carrera'), (8, 'matrícula anulada por retracto'), (9, 'matrícula anulada por otro motivo'), (10, 'No Activo'), (11, 'retiro voluntario')], default=0),
        ),
    ]