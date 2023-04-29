from datetime import datetime

from django.core.management.base import BaseCommand

from ucampus.api import obtener_todos_horarios

from curso.models import Curso, Modulo, Horario


class Command(BaseCommand):
    def handle(self, *args, **options):
        importar_horario_ucampus()
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


def importar_horario_ucampus():
    # crear módulos horarios
    creados = 0
    for modulo in modulos_horarios:
        _, creado = Modulo.objects.get_or_create(**modulo)

        if creado:
            creados += 1

    if creados:
        print(f'{creados} modulos horarios creados\n')

    tipos_clases = {
        'Cátedra': 0,
        'Laboratorio': 2,
        'Taller': 3,
        'Práctica': 4,
    }

    # registrar horario cursos
    horarios = obtener_todos_horarios()
    creados = 0
    actualizados = 0
    for fila in horarios:

        # obtener curso
        id_curso = fila['id_curso']
        try:
            curso = Curso.objects.get(id_ucampus=id_curso)
        except Curso.DoesNotExist:
            print(f'no existe un curso con id ucampus {id_curso}')
            continue
        except Curso.MultipleObjectsReturned:
            print(f'existe más de un curso con id ucampus {id_curso}')
            continue

        # obtener modulo
        hora_inicio = datetime.strptime(fila['hora_ini'], '%H:%M').time()
        hora_termino = datetime.strptime(fila['hora_fin'], '%H:%M').time()
        try:
            modulo = Modulo.objects.get(hora_inicio=hora_inicio, hora_termino=hora_termino)
        except Modulo.DoesNotExist:
            print(f'no existe un modulo con horario {hora_inicio}-{hora_termino}')
            continue

        dia = fila['dia']
        tipo_clase = tipos_clases.get(fila['tipo_clase'], 5)  # 5: otro
        sala = ''
        if 'salas' in fila:
            sala = fila['salas']

        _, creado = Horario.objects.update_or_create(
            curso=curso, dia=dia, modulo=modulo,
            defaults={
                'tipo_horario': tipo_clase,
                'sala': sala,
            }
        )

        if creado:
            creados += 1
        else:
            actualizados += 1

    print(f'{creados} horarios registrados, {actualizados} actualizados\n')

    return
