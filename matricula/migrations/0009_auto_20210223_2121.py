# Generated by Django 3.1.2 on 2021-02-24 00:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('matricula', '0008_auto_20210222_1407'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='arancelestudiante',
            name='estado',
        ),
        migrations.RemoveField(
            model_name='matriculaestudiante',
            name='estado',
        ),
        migrations.RemoveField(
            model_name='tneestudiante',
            name='estado',
        ),
    ]
