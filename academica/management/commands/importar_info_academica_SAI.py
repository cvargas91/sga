import json

from django.core.management.base import BaseCommand

from academica.models import Departamento, Ramo, Carrera, Plan
from curso.models import Periodo, Curso


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str)

    def handle(self, *args, **options):
        importar_info_academica_SAI(options['archivo'])
        return


def importar_info_academica_SAI(archivo: str):
    with open(archivo, 'r', encoding='utf-8') as archivo_dump:
        info_academica = json.load(archivo_dump)

    # parsear datos
    departamentos = []
    ramos = []
    periodos = []
    cursos = []
    carreras = []
    planes = []

    for fila in info_academica:
        if fila['model'] == 'app.institucion':
            departamentos.append(fila)

        if fila['model'] == 'app.carrera':
            carreras.append(fila)

        if fila['model'] == 'app.plan':
            planes.append(fila)

        if fila['model'] == 'app.periodo_academico':
            periodos.append(fila)

        if fila['model'] == 'app.ramo':
            ramos.append(fila)

        if fila['model'] == 'app.curso':
            cursos.append(fila)

    # cargar departamentos
    creados = 0
    for fila in departamentos:
        nombre = fila['fields']['nombre']

        _, creado = Departamento.objects.update_or_create(
            nombre=nombre,
            defaults={
                'id_ucampus': fila['fields']['ucampus_id'],
                'id_SAI': fila['pk'],
            }
        )

        if creado:
            creados += 1

    print(f'{creados} departamentos creados')

    # cargar carreras
    creados = 0
    for fila in carreras:
        try:
            depto = Departamento.objects.get(id_SAI=fila['fields']['institucion'])
        except Departamento.DoesNotExist:
            print(f"no existe un depto con id '{fila['fields']['institucion']}'")
            continue

        try:
            carrera = Carrera.objects.get(nombre=fila['fields']['nombre'])

            if carrera.departamento != depto:
                print(f"carrera '{carrera.nombre}' tiene depto mal guardado")

            carrera.id_SAI = fila['pk']
            carrera.id_ucampus = fila['fields']['ucampus_id']
            carrera.codigo_ucampus = fila['fields']['codigo_ucampus']

            carrera.save()
            creados += 1

        except Carrera.DoesNotExist:
            print(f"no existe una carrera '{fila['fields']['nombre']}' (id {fila['pk']})")

    print(f'{creados} carreras actualizadas')

    # cargar planes
    creados = 0
    for fila in planes:
        try:
            carrera = Carrera.objects.get(id_SAI=fila['fields']['carrera'])
        except Carrera.DoesNotExist:
            print(f"no existe una carrera con id '{fila['fields']['carrera']}'")
            continue

        try:
            plan = Plan.objects.get(carrera=carrera, version=fila['fields']['version'])
            plan.id_SAI = fila['pk']
            plan.id_ucampus = fila['fields']['ucampus_id']

            plan.save()
            creados += 1

        except Plan.DoesNotExist:
            print(f"no existe un plan '{carrera}'")

    print(f'{creados} planes actualizados')

    # cargar ramos
    creados = 0
    for fila in ramos:
        codigo = fila['fields']['codigo']

        departamento = None
        id_departamento = fila['fields']['institucion']
        if id_departamento:
            try:
                departamento = Departamento.objects.get(id_SAI=id_departamento)
            except Departamento.DoesNotExist:
                print(f"departamento con id_SAI {departamento} no encontrado")

        _, creado = Ramo.objects.update_or_create(
            codigo=codigo,
            defaults={
                'nombre': fila['fields']['nombre'],
                'creditos': fila['fields']['sct'],
                'id_ucampus': fila['fields']['ucampus_id'],
                'id_SAI': fila['pk'],
                'departamento': departamento,
            },
        )

        if creado:
            creados += 1

    print(f'{creados} ramos creados')

    # cargar requisitos cuando ya están todos los ramos creados
    for fila in ramos:
        requisitos = fila['fields']['requisitos']

        if requisitos:
            ramo = Ramo.objects.get(codigo=fila['fields']['codigo'])

            if requisitos.find('/') > -1:
                print(f'requisitos opcionales no soportados ({requisitos})')
                continue

            codigos = requisitos.split(',')
            for codigo in codigos:
                try:
                    ramo.requisitos.add(Ramo.objects.get(codigo=codigo))
                except Ramo.DoesNotExist:
                    print(f'ramo con codigo {codigo} no encontrado')

    # cargar periodos
    creados = 0
    for fila in periodos:
        if fila['model'] == 'app.periodo_academico':
            ano = fila['fields']['anio']
            numero = fila['fields']['semestre']

            _, creado = Periodo.objects.update_or_create(
                ano=ano,
                numero=numero,
                defaults={
                    'activo': False,
                    'id_ucampus': fila['fields']['id_periodo'],
                    'id_SAI': fila['pk'],
                },
            )

            if creado:
                creados += 1

    print(f'{creados} periodos creados')

    # cargar cursos
    creados = 0
    for fila in cursos:
        periodo = Periodo.objects.get(id_SAI=fila['fields']['periodo'])
        ramo = Ramo.objects.get(id_SAI=fila['fields']['ramo'])
        seccion = fila['fields']['seccion']

        _, creado = Curso.objects.update_or_create(
            ramo=ramo, periodo=periodo, seccion=seccion,
            defaults={
                'cupo': fila['fields']['cupo'],
                'creditos': fila['fields']['sct'],
                'id_ucampus': fila['fields']['ucampus_id'],
                'id_SAI': fila['pk'],
            },
        )

        if creado:
            creados += 1

    print(f'{creados} cursos creados')
    return
