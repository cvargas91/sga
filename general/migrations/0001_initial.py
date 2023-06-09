# Generated by Django 3.1.2 on 2020-12-15 16:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comuna',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'comuna',
            },
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'region',
            },
        ),
        migrations.CreateModel(
            name='Sede',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('direccion_texto', models.CharField(max_length=200)),
                ('direccion_comuna', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='general.comuna')),
            ],
            options={
                'db_table': 'sede',
            },
        ),
        migrations.CreateModel(
            name='Espacio',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('capacidad', models.PositiveSmallIntegerField()),
                ('sede', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='general.sede')),
            ],
            options={
                'db_table': 'espacio',
            },
        ),
        migrations.AddField(
            model_name='comuna',
            name='region',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='general.region'),
        ),
    ]
