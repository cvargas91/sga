# Generated by Django 4.0.3 on 2022-04-19 17:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('persona', '0015_agregar_estado_trans_interna'),
    ]

    operations = [
        migrations.AddField(
            model_name='estudiante',
            name='estudiante_antiguo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='estudiantes_antiguos', to='persona.estudiante'),
        ),
    ]
