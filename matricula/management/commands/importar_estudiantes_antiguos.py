import csv
import os

from django.core.management.base import BaseCommand

from academica.models import Plan
from curso.models import Periodo
from persona.models import Persona, Estudiante, EstadoEstudiante
from matricula.models import (
    ProcesoMatricula, GratuidadEstudiante, InhabilitantesMatricula,
)


class Command(BaseCommand):
    help = '''Importa los archivos de estudiantes antiguos para el proceso de matrícula'''

    def add_arguments(self, parser):
        parser.add_argument('carpeta_archivos', type=str)
        parser.add_argument('-log-level', type=str, choices=range(2), default=1)

    def handle(self, *args, **options):
        importar_estudiantes_antiguos(options['carpeta_archivos'], log_level=options['log_level'])
        return


def importar_estudiantes_antiguos(carpeta: str, log_level=1):
    # buscar archivos
    for archivo in os.listdir(carpeta):
        nombre = archivo.lower()
        if 'planes_alums' in nombre:
            path_archivo_estudiantes = os.path.join(carpeta, archivo)
        if 'finanzas' in nombre:
            path_archivo_finanzas = os.path.join(carpeta, archivo)
        if 'biblioteca' in nombre:
            path_archivo_biblioteca = os.path.join(carpeta, archivo)
        if 'gratuidad' in nombre:
            path_archivo_gratuidad = os.path.join(carpeta, archivo)

    personas_no_encontradas = 0
    registros_no_encontrados = 0
    modificados = 0
    with open(path_archivo_estudiantes, 'r', encoding='utf-8') as archivo_estudiantes:
        estudiantes = csv.DictReader(archivo_estudiantes, delimiter=';')

        for estudiante in estudiantes:
            try:
                rut = estudiante['P_AL_RUT_ALUM']
                persona = Persona.objects.get(numero_documento=rut)
                planes = Plan.objects.filter(carrera__id_ucampus=estudiante['P_AL_C_CARRERA'])

                if not planes.exists():
                    if estudiante['P_AL_LICENCIATURA'] != '0' and log_level >= 2:
                        print(f"carrera con id {estudiante['P_AL_C_CARRERA']} no existe")
                    continue

                estud = Estudiante.objects.get(persona=persona, plan__in=planes)
                estado = EstadoEstudiante.objects.get(id_ucampus=estudiante['P_AL_E_PLAN_ALUM'])

                if estud.estado_estudiante != estado:
                    if log_level >= 1:
                        print(
                            f'cambio de estado {persona.numero_documento}: '
                            f'{estud.estado_estudiante} -> {estado}'
                        )

                    estud.estado_estudiante = estado
                    estud.save()
                    modificados += 1

                if estudiante['P_AL_SEME_FIN'] != 'NULL' and not estud.periodo_egreso:
                    periodo = Periodo.objects.get(
                        ano=estudiante['P_AL_SEME_FIN'][:-1],
                        numero=estudiante['P_AL_SEME_FIN'][-1],
                    )
                    estud.periodo_egreso = periodo
                    estud.save()

                    if log_level >= 1:
                        print(f"agrega semestre fin: {estudiante['P_AL_SEME_FIN']}")

            except Persona.DoesNotExist:
                personas_no_encontradas += 1
                if log_level >= 2:
                    print(f"persona con rut {rut} no existe")

            except Estudiante.DoesNotExist:
                registros_no_encontrados += 1
                if log_level >= 2:
                    print(f"estudiante {persona}-{planes.first().carrera} no existe")

            except EstadoEstudiante.DoesNotExist:
                if log_level >= 1:
                    print(f"estado con id {estudiante['P_AL_C_CARRERA']} no existe")

    print('\narchivo estudiantes listo')
    print(f'{modificados} estudiantes actualizados')
    print(f'{personas_no_encontradas} personas no encontradas')
    print(f'{registros_no_encontrados} estudiantes no encontrados')

    # crear gratuidad estudiante e inhabilitantes estudiantes
    proceso_matricula = ProcesoMatricula.objects.get(activo=True)
    estudiantes_antiguos = Estudiante.objects.exclude(
        periodo_ingreso=proceso_matricula.periodo_ingreso,
    ).filter(
        estado_estudiante_id__in=[4, 1],  # regular o congelado
    )
    modificados = 0

    for estudiante_antiguo in estudiantes_antiguos:
        InhabilitantesMatricula.objects.update_or_create(
            estudiante=estudiante_antiguo,
            proceso_matricula=proceso_matricula,
            defaults={
                'tiene_deuda_finanzas': False,
                'comentario_finanzas': '',
                'tiene_deuda_biblioteca': False,
                'comentario_biblioteca': '',
            }
        )
        GratuidadEstudiante.objects.update_or_create(
            estudiante=estudiante_antiguo,
            proceso_matricula=proceso_matricula,
            defaults={'tiene_gratuidad': False}
        )
        modificados += 1

    print(f'\ninhabilitantes y gratuidad creados para {modificados} estudiantes antiguos\n')

    # cargar deudas biblioteca
    modificados = 0
    personas_no_encontradas = 0
    with open(path_archivo_biblioteca, 'r', encoding='utf-8') as archivo_biblioteca:
        deudas_biblioteca = csv.DictReader(archivo_biblioteca, delimiter=',')

        for fila in deudas_biblioteca:
            try:
                # obtener inhabilitantes de la persona
                rut = fila['Rut'][:-1]
                persona = Persona.objects.get(numero_documento=rut)
                inhabilitantes = InhabilitantesMatricula.objects.filter(
                    proceso_matricula=proceso_matricula,
                    estudiante__persona=persona,
                )
                modificados += 1

                # actualizar comentario
                for inhabilitante in inhabilitantes:

                    inhabilitante.tiene_deuda_biblioteca = True
                    inhabilitante.comentario_biblioteca += (
                        f'Debe {fila["Titulo"]}. '
                    )
                    inhabilitante.save()

            except Persona.DoesNotExist:
                personas_no_encontradas += 1
                if log_level >= 1:
                    print(f'persona con rut {rut} no existe')

    print('archivo biblioteca listo')
    print(f'{modificados} deudas registradas')
    print(f'{personas_no_encontradas} personas no encontradas\n')

    # cargar deudas finanzas
    modificados = 0
    personas_no_encontradas = 0
    with open(path_archivo_finanzas, 'r', encoding='utf-8') as archivo_finanzas:
        deudas_finanzas = csv.DictReader(archivo_finanzas, delimiter=',')

        for fila in deudas_finanzas:
            try:
                # obtener inhabilitantes de la persona
                rut = fila['DOCUMENTO']
                persona = Persona.objects.get(numero_documento=rut)
                inhabilitantes = InhabilitantesMatricula.objects.filter(
                    proceso_matricula=proceso_matricula,
                    estudiante__persona=persona,
                )
                modificados += 1

                # actualizar comentario
                for inhabilitante in inhabilitantes:

                    inhabilitante.tiene_deuda_finanzas = True
                    # inhabilitante.comentario_finanzas += (
                    #     f'Debe {fila["Saldo 2022"]} por la carrera {fila["PLAN"]}. '
                    # )
                    inhabilitante.save()

            except Persona.DoesNotExist:
                personas_no_encontradas += 1
                if log_level >= 1:
                    print(f'persona con rut {rut} no existe')

    print('archivo finanzas listo')
    print(f'{modificados} deudas registradas')
    print(f'{personas_no_encontradas} personas no encontradas\n')

    # cargar gratuidad
    modificados = 0
    personas_no_encontradas = 0
    registros_no_encontrados = 0
    with open(path_archivo_gratuidad, 'r', encoding='utf-8') as archivo_biblioteca:
        gratuidad_estudiantes = csv.DictReader(archivo_biblioteca, delimiter=';')

        for fila in gratuidad_estudiantes:
            try:
                # obtener gratuidad de la persona
                rut = fila['numero_documento']
                persona = Persona.objects.get(numero_documento=rut)
                gratuidades = GratuidadEstudiante.objects.filter(
                    proceso_matricula=proceso_matricula,
                    estudiante__persona=persona,
                )

                if not gratuidades.exists():
                    estado = Estudiante.objects.filter(persona=persona).first().estado_estudiante

                    if estado.id in [1, 4]:  # estudiante regular o postergado sin registro
                        registros_no_encontrados += 1
                        if log_level >= 1:
                            print(f'no se ha encontrado un registro para el rut {rut}')

                # actualizar gratuidad
                if fila['GRATUIDAD'] == '1':
                    for gratuidad in gratuidades:
                        gratuidad.tiene_gratuidad = True
                        gratuidad.save()
                        modificados += 1

            except Persona.DoesNotExist:
                personas_no_encontradas += 1
                if log_level >= 1:
                    print(f'persona con rut {rut} no existe')

    print('archivo gratuidad listo')
    print(f'{modificados} gratuidades actualizadas')
    print(f'{personas_no_encontradas} personas no encontradas')
    print(f'{registros_no_encontrados} registros no encontrados')
    return
