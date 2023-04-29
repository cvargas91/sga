# Generated by Django 4.1.3 on 2023-01-13 19:08

from django.db import migrations, models
import persona.models


class Migration(migrations.Migration):

    dependencies = [
        ('persona', '0020_persona_archivo_contrato'),
    ]

    operations = [
        migrations.AlterField(
            model_name='persona',
            name='archivo_contrato',
            field=models.FilePathField(blank=True, null=True, path=persona.models.dir_contratos),
        ),
    ]
