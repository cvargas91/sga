# Generated by Django 3.1.6 on 2021-02-18 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pagos', '0002_auto_20210218_0938'),
    ]

    operations = [
        migrations.AddField(
            model_name='productos',
            name='observaciones_codigo_interno',
            field=models.CharField(max_length=200, null=True),
        ),
    ]