# Generated by Django 3.1.2 on 2021-06-09 16:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curso', '0002_auto_20201211_1534'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodo',
            name='fecha_fin',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='periodo',
            name='fecha_inicio',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='periodo',
            name='link_decreto',
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
