# Generated by Django 4.1.3 on 2023-01-13 14:56

from django.db import migrations, models
import persona.models


class Migration(migrations.Migration):

    dependencies = [
        ('persona', '0019_persona_acepta_contrato'),
    ]

    operations = [
        migrations.AddField(
            model_name='persona',
            name='archivo_contrato',
            field=models.FilePathField(null=True, path=persona.models.dir_contratos),
        ),
    ]