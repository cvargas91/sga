# Generated by Django 4.0 on 2022-04-19 19:05
from django.db import migrations

grupos = ['Administradores', 'Estudiantes']


def crear_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for grupo in grupos:
        Group.objects.get_or_create(name=grupo)
    return


def eliminar_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=grupos).delete()
    return


def asignar_estudiantes(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Estudiante = apps.get_model('persona', 'Estudiante')

    grupo_estudiantes = Group.objects.get(name='Estudiantes')
    for estudiante in Estudiante.objects.all():
        estudiante.persona.user.groups.add(grupo_estudiantes)
    return


class Migration(migrations.Migration):

    dependencies = [
        ('persona', '0016_estudiante_estudiante_antiguo'),
    ]

    operations = [
        migrations.RunPython(crear_grupos, eliminar_grupos),
        migrations.RunPython(asignar_estudiantes, migrations.RunPython.noop),
    ]
