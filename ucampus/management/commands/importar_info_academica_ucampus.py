import re

from django.core.management.base import BaseCommand

from ucampus.api import (
    obtener_carreras, obtener_planes, obtener_ramos, obtener_todos_cursos, TIPOS_CARRERAS_UCAMPUS,
)

from academica.models import Departamento, Ramo, Carrera, Plan
from curso.models import Periodo, Curso


class Command(BaseCommand):
    def handle(self, *args, **options):
        importar_info_academica_ucampus()
        return


def importar_info_academica_ucampus():
    # agregar id ucampus a periodos
    for periodo in Periodo.objects.all():
        if not periodo.id_ucampus:
            periodo.id_ucampus = f'{periodo.ano}.{periodo.numero}'
            periodo.save()

    # cargar carreras
    carreras = obtener_carreras()
    print(len(carreras), 'carreras obtenidas')

    creados = 0
    actualizados = 0
    for fila in carreras:
        try:
            depto = Departamento.objects.get(id_ucampus=fila['id_institucion'])
        except Departamento.DoesNotExist:
            print(
                f"no existe un depto con id '{fila['id_institucion']}' ({fila['institucion']})\n"
                f"\tcarrera: {fila['nombre']}"
            )
            continue

        _, creado = Carrera.objects.update_or_create(
            nombre=fila['nombre'],
            defaults={
                'departamento': depto,
                'tipo_carrera': TIPOS_CARRERAS_UCAMPUS[fila['tipo_titulo']],
                'id_ucampus': fila['id_carrera'],
                'codigo_ucampus': fila['codigo_carrera'],
            },
        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print(f'\n{creados} carreras creadas, {actualizados} actualizadas\n')

    # cargar planes
    planes = obtener_planes()
    print(len(planes), 'planes obtenidos')

    creados = 0
    actualizados = 0
    for fila in planes:
        try:
            carrera = Carrera.objects.get(id_ucampus=fila['id_carrera'])
        except Carrera.DoesNotExist:
            print(
                f"no existe una carrera con id '{fila['id_carrera']}'\n"
                f"\tplan: {fila['nombre']}"
            )
            continue

        _, creado = Plan.objects.update_or_create(
            carrera=carrera, version=fila['version'],
            defaults={
                'id_ucampus': fila['id_plan'],
            },
        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print(f'\n{creados} planes creados, {actualizados} actualizados\n')

    # cargar ramos
    ramos = obtener_ramos()
    print(len(ramos), 'ramos obtenidos')

    creados = 0
    actualizados = 0
    for fila in ramos:
        codigo = fila['codigo']

        departamento = None
        id_departamento = fila['id_institucion']
        if id_departamento:
            try:
                departamento = Departamento.objects.get(id_ucampus=id_departamento)
            except Departamento.DoesNotExist:
                print(f"departamento con id_ucampus {id_departamento} no encontrado")

        _, creado = Ramo.objects.update_or_create(
            codigo=codigo,
            defaults={
                'nombre': fila['nombre'],
                'creditos': fila['sct'],
                'id_ucampus': fila['id_ramo'],
                'departamento': departamento,
            },
        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print(f'\n{creados} ramos creados, {actualizados} actualizados\n')

    # cargar requisitos/equivalencias cuando ya están todos los ramos creados
    for fila in ramos:

        requisitos = fila['requisito']
        if requisitos:
            ramo = Ramo.objects.get(codigo=fila['codigo'])

            if requisitos.find('/') > -1:
                print(f"requisitos opcionales no soportados {requisitos} ({fila['nombre']})")
                continue

            codigos = requisitos.split(',')
            for codigo in codigos:
                try:
                    ramo.requisitos.add(Ramo.objects.get(codigo=codigo))
                except Ramo.DoesNotExist:
                    print(f"ramo con codigo {codigo} no encontrado ({fila['nombre']})")

        equivalencias = fila['equivalencia']
        if equivalencias:
            ramo = Ramo.objects.get(codigo=fila['codigo'])

            codigos = re.split('/|,', equivalencias)
            for codigo in codigos:
                try:
                    ramo.equivalencias.add(Ramo.objects.get(codigo=codigo))
                except Ramo.DoesNotExist:
                    print(f"ramo con codigo {codigo} no encontrado ({fila['nombre']})")

    # cargar cursos
    cursos = obtener_todos_cursos()
    print(len(cursos), 'cursos obtenidos')

    creados = 0
    actualizados = 0
    for fila in cursos:
        periodo = Periodo.objects.get(id_ucampus=fila['id_periodo'])
        ramo = Ramo.objects.get(id_ucampus=fila['id_ramo'])
        seccion = fila['seccion']

        _, creado = Curso.objects.update_or_create(
            ramo=ramo, periodo=periodo, seccion=seccion,
            defaults={
                'cupo': fila['cupo'],
                'creditos': fila['sct'],
                'id_ucampus': fila['id_curso'],
            },
        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print(f'\n{creados} cursos creados, {actualizados} actualizados')
    return
