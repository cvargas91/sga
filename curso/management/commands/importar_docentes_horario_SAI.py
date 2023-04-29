from datetime import datetime
import json

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from persona.models import Persona
from curso.models import Curso, DocenteCurso, Modulo, Horario


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str)

    def handle(self, *args, **options):
        importar_docentes_SAI(options['archivo'])
        return


modulos_horarios = [
    {
        "hora_inicio": "08:30",
        "hora_termino": "10:00",
    },
    {
        "hora_inicio": "10:15",
        "hora_termino": "11:45",
    },
    {
        "hora_inicio": "12:00",
        "hora_termino": "13:30",
    },
    {
        "hora_inicio": "14:30",
        "hora_termino": "16:00",
    },
    {
        "hora_inicio": "16:15",
        "hora_termino": "17:45",
    },
    {
        "hora_inicio": "18:00",
        "hora_termino": "19:30",
    }
]


def importar_docentes_SAI(archivo: str):
    with open(archivo, 'r', encoding='utf-8') as archivo_dump:
        archivo_docentes = json.load(archivo_dump)

    # obtener academicos en cursos y separar archivo
    ids_docentes = set()
    funcionarios = []
    docentes_en_cursos = []
    horario = []

    for fila in archivo_docentes:
        if fila['model'] == 'app.academico_en_curso':
            ids_docentes.add(fila['fields']['academico'])
            docentes_en_cursos.append(fila)

        if fila['model'] == 'app.funcionario':
            funcionarios.append(fila)

        if fila['model'] == 'app.horario':
            horario.append(fila)

    print(f'{len(ids_docentes)} docentes detectados entre {len(funcionarios)} funcionarios')

    sexos = {
        1: 1,  # masculino
        2: 0,  # femenino
        None: 2,  # no especifica
    }

    # crear grupo para docentes si no existe
    grupo_docentes, _ = Group.objects.get_or_create(name='Docentes')

    # crear docentes
    docentes = {}
    creados = 0
    actualizados = 0
    for fila in funcionarios:
        id_SAI = fila['pk']
        docente = fila['fields']

        if id_SAI in ids_docentes:
            rut = docente['rut_num']

            usuario, _ = User.objects.get_or_create(username=rut)

            if docente['nombre2']:
                nombres = f"{docente['nombre1']} {docente['nombre2']}"
            else:
                nombres = docente['nombre1']

            fecha_nacimiento = None
            if docente['fecha_nacimiento']:
                try:
                    fecha_nacimiento = datetime.strptime(
                        docente['fecha_nacimiento'], '%Y-%m-%d'
                    )
                except ValueError:
                    print(f'no se pudo parsear la fecha {docente["fecha_nacimiento"]}')

            # crear o actualizar persona
            persona, creada = Persona.objects.update_or_create(
                user=usuario,
                numero_documento=rut,
                defaults={
                    'tipo_identificacion': 0,  # carnet
                    'digito_verificador': docente['rut_dv'],
                    'mail_institucional': docente['email_institucional'],

                    'nombres': nombres,
                    'apellido1': docente['apellido1'],
                    'apellido2': docente['apellido2'],
                    'fecha_nacimiento': fecha_nacimiento,
                    'sexo': sexos[docente['sexo']],
                }
            )

            if docente['email']:
                persona.mail_secundario = docente['email']
            if docente['telefono']:
                persona.telefono_celular = docente['telefono']
            if docente['nombre_emergencia']:
                persona.emergencia_nombre = docente['nombre_emergencia']
            if docente['telefono_emergencia']:
                persona.emergencia_telefono_celular = docente['telefono_emergencia']

            # registrar grupo y guardar persona
            usuario.groups.add(grupo_docentes)
            docentes[id_SAI] = persona

            if creada:
                creados += 1
            else:
                actualizados += 1

    print(f'{creados} docentes creados, {actualizados} actualizados\n')

    # registrar docentes en cursos
    creados = 0
    for fila in docentes_en_cursos:
        docente = docentes.get(fila['fields']['academico'], None)
        id_curso = fila['fields']['curso']

        if id_curso and docente:
            try:
                curso = Curso.objects.get(id_SAI=id_curso)
            except Curso.MultipleObjectsReturned:
                print(f'existe más de un curso con id SAI {id_curso}')
                continue
            except Curso.DoesNotExist:
                print(f'no existe un curso con id SAI {id_curso}')
                continue

            _, creado = DocenteCurso.objects.get_or_create(curso=curso, persona=docente)

            if creado:
                creados += 1

    print(f'{creados} docentes en cursos registrados\n')

    # crear módulos horarios
    creados = 0
    for modulo in modulos_horarios:
        _, creado = Modulo.objects.get_or_create(**modulo)

        if creado:
            creados += 1

    print(f'{creados} modulos horarios creados\n')

    tipos_clases = {
        'C\u00e1tedra': 0,
        'Laboratorio': 2,
        'Taller': 3,
    }

    # registrar horario cursos
    creados = 0
    for fila in horario:
        id_curso = fila['fields']['curso']
        pk = fila['pk']

        if not id_curso:
            continue

        try:
            curso = Curso.objects.get(id_SAI=id_curso)
        except Curso.MultipleObjectsReturned:
            print(f'existe más de un curso con id SAI {id_curso} (pk {pk})')
            continue
        except Curso.DoesNotExist:
            print(f'no existe un curso con id SAI {id_curso} (pk {pk})')
            continue

        hora_inicio = datetime.strptime(fila['fields']['hora_inicio'], '%H:%M').time()
        hora_termino = datetime.strptime(fila['fields']['hora_fin'], '%H:%M').time()

        try:
            modulo = Modulo.objects.get(hora_inicio=hora_inicio, hora_termino=hora_termino)
        except Modulo.DoesNotExist:
            print(f'no existe un modulo con horario {hora_inicio}-{hora_termino} (pk {pk})')
            continue

        dia = fila['fields']['dia']
        tipo_clase = fila['fields']['tipo_clase']
        sala = fila['fields']['salas']

        _, creado = Horario.objects.get_or_create(
            curso=curso, dia=dia, modulo=modulo,
            defaults={
                'tipo_horario': tipos_clases.get(tipo_clase),  # carnet
                'sala': sala,
            }
        )

        if creado:
            creados += 1

    print(f'{creados} horarios registrados\n')

    return
