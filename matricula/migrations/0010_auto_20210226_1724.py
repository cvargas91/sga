# Generated by Django 3.1.2 on 2021-02-26 20:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pagare', '0001_initial'),
        ('matricula', '0009_auto_20210223_2121'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='arancelestudiante',
            name='pagare_estudiante',
        ),
        migrations.AddField(
            model_name='arancelestudiante',
            name='pagare',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='arancel', to='pagare.pagare'),
        ),
    ]