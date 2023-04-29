from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import IntegrityError

from ucampus.api import obtener_todos_cursos_dictados, obtener_personas

from persona.permisos import GRUPOS

from persona.models import Persona
from curso.models import Curso, DocenteCurso, AyudanteCurso


class Command(BaseCommand):

    def handle(self, *args, **options):
        importar_docentes_ucampus()
        return


sexos = {
    'Masculino': 1,  # masculino
    'Femenino': 0,  # femenino
    '': 2,  # no especifica
}


def crear_persona_ucampus(fila):
    rut = fila['rut']

    usuario, _ = User.objects.get_or_create(username=rut)

    if fila['nombre2']:
        nombres = f"{fila['nombre1']} {fila['nombre2']}"
    else:
        nombres = fila['nombre1']

    fecha_nacimiento = None
    if fila['fecha_nacimiento']:
        try:
            fecha_nacimiento = datetime.strptime(fila['fecha_nacimiento'], '%Y-%m-%d')
        except ValueError:
            print(f'no se pudo parsear la fecha {fila["fecha_nacimiento"]}')

    # crear persona
    try:
        persona = Persona.objects.create(
            user=usuario,
            tipo_identificacion=0,  # carnet
            numero_documento=rut,
            digito_verificador=fila['dv'],

            nombres=nombres,
            apellido1=fila['apellido1'],
            apellido2=fila['apellido2'],
            fecha_nacimiento=fecha_nacimiento,
            sexo=sexos[fila['genero']],
        )

        if fila['email']:
            persona.mail_secundario = fila['email']
        if fila['telefono'] and len(fila['telefono']) <= 20:
            persona.telefono_celular = fila['telefono']
        persona.save()          # ésta llamada podría estar duplicada
    except IntegrityError:
        print(f'Persona rut: {rut} repetida')
    return


def importar_docentes_ucampus():
    cursos_dictados = obtener_todos_cursos_dictados()

    # buscar personas nuevas
    ruts_existentes = Persona.objects.all().values_list('numero_documento', flat=True)
    ruts_docentes = set([str(fila['rut']) for fila in cursos_dictados])
    ruts_nuevos = [rut for rut in ruts_docentes if rut not in ruts_existentes]

    personas_nuevas = obtener_personas(ruts_nuevos)
    creados = 0
    for fila in personas_nuevas:
        crear_persona_ucampus(fila)
        creados += 1

    if creados:
        print(f'{creados} personas nuevas registradas\n')

    # asignar grupos y crear diccionario
    grupo_docentes, _ = Group.objects.get_or_create(name=GRUPOS.DOCENTES)
    docentes = {}
    for rut in ruts_docentes:
        usuario = User.objects.get(username=rut)

        # registrar grupo y guardar persona
        usuario.groups.add(grupo_docentes)
        docentes[rut] = usuario.persona

    # registrar docentes en cursos
    roles = {
        'Profesor de Cátedra': 1,
        'Profesor Colaborador': 3,
    }

    creados = 0
    actualizados = 0
    for fila in cursos_dictados:
        docente = docentes.get(str(fila['rut']), None)
        id_curso = fila['id_curso']

        if not id_curso:
            print(f'no existe un curso con id ucampus {id_curso}')
            continue

        if not docente:
            print(f"no existe un docente con rut {fila['rut']}")
            continue

        try:
            curso = Curso.objects.get(id_ucampus=id_curso)
        except Curso.DoesNotExist:
            print(f'no existe un curso con id ucampus {id_curso}')
            continue
        except Curso.MultipleObjectsReturned:
            print(f'existe más de un curso con id ucampus {id_curso}')
            continue

        if fila['cargo'] == 'Ayudante':
            _, creado = AyudanteCurso.objects.update_or_create(curso=curso, persona=docente)

        else:
            rol = roles.get(fila['cargo'], 1)
            _, creado = DocenteCurso.objects.update_or_create(
                curso=curso, persona=docente, defaults={'rol': rol}
            )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print(f'{creados} docentes en cursos registrados, {actualizados} actualizados\n')
    return
