# Generated by Django 3.1.2 on 2021-05-04 04:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academica', '0004_carrera_tipo_carrera'),
        ('matricula', '0020_auto_20210503_2038'),
    ]

    operations = [
        migrations.AddField(
            model_name='periodoprocesomatricula',
            name='planes',
            field=models.ManyToManyField(to='academica.Plan'),
        ),
    ]
