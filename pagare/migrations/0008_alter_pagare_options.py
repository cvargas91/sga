# Generated by Django 4.0 on 2022-01-19 18:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pagare', '0007_pagare_documento_escaneado'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pagare',
            options={'permissions': [('recibir_pagare', 'Puede marcar pagarés como recibidos')]},
        ),
    ]
