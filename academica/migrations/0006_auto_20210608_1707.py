# Generated by Django 3.1.2 on 2021-06-08 21:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academica', '0005_plan_link_decreto'),
    ]

    operations = [
        migrations.AddField(
            model_name='carrera',
            name='id_SAI',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='carrera',
            name='id_ucampus',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='plan',
            name='codigo_sies',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='plan',
            name='id_SAI',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='plan',
            name='id_ucampus',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='plan',
            name='codigo_demre',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]