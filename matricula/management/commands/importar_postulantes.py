import csv
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ProtectedError

from academica.models import Plan
from persona.models import Persona
from general.models import Comuna
from matricula.models import PostulanteDefinitivo, ProcesoMatricula, ViaIngreso


class Command(BaseCommand):
    help = '''Importa el archivo de postulantes de un proceso'''

    def add_arguments(self, parser):
        parser.add_argument('carpeta_archivos', type=str)

        parser.add_argument(
            '--eliminar',
            action='store_true',
            help='Elimina todos los usuarios creados por este comando',
        )

    def handle(self, *args, **options):
        if options['eliminar']:
            limpiar_postulantes(options['carpeta_archivos'])

        else:
            importar_postulantes(options['carpeta_archivos'])

        return


delim = ','


def importar_postulantes(carpeta: str):
    # buscar archivos
    for archivo in os.listdir(carpeta):
        nombre = archivo.lower()
        if 'persona' in nombre:
            nombre_archivo_persona = os.path.join(carpeta, archivo)
        if 'matricula' in nombre:
            nombre_archivo_matricula = os.path.join(carpeta, archivo)
        if 'gratuidad' in nombre:
            nombre_archivo_gratuidad = os.path.join(carpeta, archivo)

    with open(nombre_archivo_persona, 'r', encoding='utf-8') as archivo_personas:
        personas = csv.DictReader(archivo_personas, delimiter=delim)

        for fila in personas:
            usuario, creado = User.objects.get_or_create(username=fila['numero_documento'])

            try:
                tipo_identificacion = {
                    '': 0,
                    'C': 0,
                    'P': 1,
                }
                sexos = {
                    '': 2,
                    '0': 2,  # no especifica
                    '1': 1,  # masculino
                    '2': 0,  # femenino
                }

                persona, _ = Persona.objects.update_or_create(
                    user=usuario,
                    defaults={
                        'tipo_identificacion': tipo_identificacion[fila['tipo_identificacion']],
                        'numero_documento': fila['numero_documento'],
                        'digito_verificador': fila['dv'],

                        'apellido1': fila['primer_apellido'].title(),
                        'apellido2': fila['segundo_apellido'].title(),
                        'nombres': fila['nombres'].title(),
                        'sexo': sexos[fila['sexo']],

                        'telefono_celular': fila['numero_de_celular'],
                        'mail_secundario': fila['email'],

                        'direccion_calle': fila['calle'].lower(),
                        'direccion_numero': fila['numero'].lower(),
                        'direccion_depto': fila['departamento'].lower(),
                    }
                )

                fecha = fila['fecha_nacimiento']
                if fecha:
                    # detectar cuando se le elimino el primer 0 a la fecha de nacimiento y corregir
                    if len(fecha) == 7:
                        fecha = f'0{fecha}'

                    try:
                        persona.fecha_nacimiento = datetime.strptime(fecha, '%d%m%Y')
                    except ValueError:
                        print(f'no se pudo parsear la fecha {fecha}')

                if fila['codigo_comuna_d']:
                    try:
                        persona.direccion_comuna = Comuna.objects.get(
                            codigo_demre=fila['codigo_comuna_d'])
                    except ObjectDoesNotExist:
                        print(f'No se encontró la comuna {fila["codigo_comuna_d"]}')

                persona.save()

            except IntegrityError:
                print(f'persona { fila["numero_documento"] } ya existe')

    print('\npersonas listas\n')

    with open(nombre_archivo_matricula, 'r', encoding='utf-8') as archivo_matriculas:
        matriculas = csv.DictReader(archivo_matriculas, delimiter=delim)

        resultados = {
            '24': 0,  # seleccionado
            '25': 1,  # lista de espera
        }
        proceso_matricula = ProcesoMatricula.objects.get(activo=True)

        for fila in matriculas:
            try:
                persona = Persona.objects.get(numero_documento=fila['numero_documento'])

                clave = fila['nro_tarj_matricula']
                if not clave:
                    clave = persona.numero_documento

                posicion_lista = fila['lugar_en_la_lista'] if fila['lugar_en_la_lista'] else 1

                post, _ = PostulanteDefinitivo.objects.update_or_create(
                    persona=persona,
                    proceso_matricula=proceso_matricula,
                    plan=Plan.objects.get(codigo_demre=fila['codigo']),
                    via_ingreso=ViaIngreso.objects.get(pk=fila['id_sga_via_ingreso']),

                    defaults={
                        'numero_demre': clave,
                        'resultado_postulacion': resultados[fila['estado_de_la_postulacion']],
                        'posicion_lista': posicion_lista,
                        'habilitado': fila['habilitado'] == '1',
                    }
                )

                if fila['promedio_notas']:
                    post.promedio_NEM = fila['promedio_notas'].replace(',', '.')
                if fila['ptje_nem']:
                    post.puntaje_NEM = fila['ptje_nem']
                if fila['ptje_ranking']:
                    post.puntaje_ranking = fila['ptje_ranking']
                if fila['mate_m1_max']:
                    post.puntaje_matematica_m1 = fila['mate_m1_max']
                if fila['mate_m2_max']:
                    post.puntaje_matematica_m2 = fila['mate_m2_max'] 
                if fila['clec_max']:
                    post.puntaje_lenguaje = fila['clec_max']
                if fila['hcso_max']:
                    post.puntaje_historia = fila['hcso_max']
                if fila['cien_max']:
                    post.puntaje_ciencias = fila['cien_max']
                if fila['modulo_max']:
                    post.modulo_ciencias = fila['modulo_max']
                if fila['promedio_cm_max']:
                    post.promedio_lenguaje_matematica = fila['promedio_cm_max'].replace(',', '.')
                if fila['puntaje_ponderado']:
                    post.puntaje_ponderado = fila['puntaje_ponderado'].replace(',', '.')
                if fila['p_50']:
                    post.percentil_50 = fila['p_50']
                if fila['p_60']:
                    post.percentil_60 = fila['p_60']

                post.save()

            except Persona.DoesNotExist:
                print(f'usuario con rut { fila["numero_documento"] } no existe')

            except IntegrityError:
                print(
                    f'postulante { fila["numero_documento"] } - '
                    f'{Plan.objects.get(codigo_demre=fila["codigo"])} '
                    f'({ViaIngreso.objects.get(pk=fila["id_sga_via_ingreso"])}) ya existe'
                )

    print('\npostulantes listos\n')

    with open(nombre_archivo_gratuidad, 'r', encoding='utf-8') as archivo_gratuidad:
        gratuidad = csv.DictReader(archivo_gratuidad, delimiter=delim)
        for fila in gratuidad:
            if fila['gratuidad'] == '1':
                try:
                    persona = Persona.objects.get(numero_documento=fila['numero_documento'])
                    PostulanteDefinitivo.objects.filter(persona=persona).update(
                        preseleccionado_gratuidad=True
                    )

                except ObjectDoesNotExist:
                    print(f'usuario con rut { fila["numero_documento"] } no existe')

    print('\ngratuidad lista')
    return


def limpiar_postulantes(carpeta: str):
    # buscar archivos
    for archivo in os.listdir(carpeta):
        nombre = archivo.lower()
        if 'persona' in nombre:
            nombre_archivo_persona = os.path.join(carpeta, archivo)
        if 'matricula' in nombre:
            nombre_archivo_matricula = os.path.join(carpeta, archivo)

    with open(nombre_archivo_matricula, 'r', encoding='utf-8') as archivo_matriculas:
        matriculas = csv.DictReader(archivo_matriculas, delimiter=delim)

        proceso_matricula = ProcesoMatricula.objects.get(activo=True)

        for fila in matriculas:
            try:
                persona = Persona.objects.get(numero_documento=fila['NUMERO_DOCUMENTO'])
                PostulanteDefinitivo.objects.filter(
                    persona=persona,
                    proceso_matricula=proceso_matricula,
                ).delete()

            except ObjectDoesNotExist:
                continue

            except ProtectedError:
                print(f'postulante { fila["NUMERO_DOCUMENTO"] } no puede ser eliminado'
                      f'(protegido por otras relaciones)')

    print('postulantes eliminados')

    with open(nombre_archivo_persona, 'r', encoding='utf-8') as archivo_personas:
        personas = csv.DictReader(archivo_personas, delimiter=delim)

        for fila in personas:
            try:
                usuario = User.objects.get(username=fila['NUMERO_DOCUMENTO'])
                Persona.objects.filter(user=usuario).delete()

                try:
                    usuario.delete()
                except ProtectedError:
                    print(f'usuario { fila["NUMERO_DOCUMENTO"] } no puede ser eliminado'
                          f'(protegido por otras relaciones)')

            except ObjectDoesNotExist:
                continue

            except ProtectedError:
                print(f'persona { fila["NUMERO_DOCUMENTO"] } no puede ser eliminada'
                      f'(protegido por otras relaciones)')

    print('personas eliminadas\n')
    return
