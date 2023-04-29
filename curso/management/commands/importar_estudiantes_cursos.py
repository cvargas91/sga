import json

from django.core.management.base import BaseCommand

from persona.models import Persona, Estudiante
from curso.models import Curso, EstudianteCurso, EstadoEstudianteCurso, Periodo
from academica.models import Carrera

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str)

    def handle(self, *args, **options):
        importar_estudiantes_cursos_SAI(options['archivo'])
        return


class EstudianteCarreraTemp:
    def __init__(self, fila, persona):
        self.carrera = fila['fields']['carrera']
        self.periodo_inicio = fila['fields']['periodo_inicio']
        self.periodo_fin = fila['fields']['periodo_fin']

        self.instancia = None

        try:
            self.instancia = Estudiante.objects.get(
                persona=persona, plan__carrera__id_SAI=self.carrera)

            if self.periodo_fin:
                self.instancia.periodo_egreso = Periodo.objects.get(id_SAI=self.periodo_fin)
                self.instancia.save()

        except Estudiante.DoesNotExist:
            print(f'no existe el estudiante {persona.numero_documento} - {self.carrera}')
            raise

        except Estudiante.MultipleObjectsReturned:
            print(f'existe más de un estudiante {persona.numero_documento} - {self.carrera}')
            raise

        except Periodo.DoesNotExist:
            print(f'no existe un periodo con id_SAI {self.periodo_fin}')

    def __repr__(self):
        return f'{self.instancia.plan.carrera.nombre} {self.periodo_inicio}-{self.periodo_fin}'


class EstudianteCursoTemp:
    def __init__(self, fila):
        self.pk = fila['pk']
        self.curso = fila['fields']['curso']
        self.periodo = fila['fields']['periodo']

        try:
            self.estado = EstadoEstudianteCurso.objects.get(id_SAI=fila['fields']['estado'])
        except EstadoEstudianteCurso.DoesNotExist:
            print(f'no existe un estado con id_SAI {fila["fields"]["estado"]}')
            raise

        self.nota_final = fila['fields']['nota_final']
        if self.nota_final == '':
            self.nota_final = None

        self.carrera = None

        self.instancia = None
        try:
            self.instancia = Curso.objects.get(id_SAI=self.curso)
        except Curso.DoesNotExist:
            print(f'no existe un curso con id SAI {self.curso} (alumno_curso {fila["pk"]})')

    def __repr__(self):
        return f'{self.curso}-{self.periodo}'


class EstudianteTemp:
    def __init__(self, fila):
        self.id_SAI = fila['pk']
        self.rut = fila['fields']['rut_num']
        self.carreras = []
        self.cursos = []

        self.instancia = None
        try:
            self.instancia = Persona.objects.get(numero_documento=self.rut)
        except Persona.DoesNotExist:
            print(f'No existe una persona con rut {self.rut}')
            raise

    def agregar_carrera(self, fila_carrera):
        # solo agregar títulos, no licenciaturas
        if Carrera.objects.filter(id_SAI=fila_carrera['fields']['carrera']).exists():
            self.carreras.append(EstudianteCarreraTemp(fila_carrera, self.instancia))
            self.carreras.sort(key=lambda carrera: carrera.periodo_inicio)

    def agregar_curso(self, fila_curso):
        self.cursos.append(EstudianteCursoTemp(fila_curso))

    def distribuir_cursos(self):
        # solo es necesario chequear en estudiantes con más de una carrera
        if len(self.carreras) > 1:
            print(f'{self.rut} {self.carreras}')

            for curso in self.cursos:
                carrera_curso = None
                multiple = False

                # chequear si el curso se encuentra dentro de los periodos de la carrera
                for carrera in self.carreras:
                    if carrera.periodo_inicio <= curso.periodo \
                            and (not carrera.periodo_fin or carrera.periodo_fin >= curso.periodo):

                        # chequear si es que hay colisión con otra carrera
                        if carrera_curso:

                            # periodo fin carrera anterior sobrepuesto carrera
                            if carrera.periodo_inicio == curso.periodo \
                                    and self.carreras[0].periodo_fin == curso.periodo:
                                carrera_curso = carrera.instancia

                            else:
                                print(f'curso {curso} pertenece a más de una carrera')
                                multiple = True

                        else:
                            carrera_curso = carrera.instancia

                if carrera_curso and not multiple:
                    curso.carrera = carrera_curso
                elif multiple:
                    print(f'curso {curso} no pertenece a ninguna carrera')
            print()

        else:
            for curso in self.cursos:
                curso.carrera = self.carreras[0].instancia

        return

    def __str__(self):
        return (
            f'{self.rut} ({len(self.cursos)} cursos)'
            f' carreras: {[carrera.carrera for carrera in self.carreras]}'
        )


estados_cursos = [
    {
        "nombre": "Inscrito",
        "completado": False,
        "aprobado": False,
        "id_SAI": 16,
        "id_ucampus": 0
    },
    {
        "nombre": "Aprobado",
        "completado": True,
        "aprobado": True,
        "id_SAI": 17,
        "id_ucampus": 1
    },
    {
        "nombre": "Reprobado",
        "completado": True,
        "aprobado": False,
        "id_SAI": 19,
        "id_ucampus": 7
    },
    {
        "nombre": "Postergado",
        "completado": False,
        "aprobado": False,
        "id_SAI": None,
        "id_ucampus": None
    },
    {
        "nombre": "Anulado",
        "completado": False,
        "aprobado": False,
        "id_SAI": None,
        "id_ucampus": None
    }
]


def importar_estudiantes_cursos_SAI(archivo: str):
    with open(archivo, 'r', encoding='utf-8') as archivo_dump:
        archivo_estudiantes_cursos = json.load(archivo_dump)

    # crear estados curso estudiante
    creados = 0
    for estado in estados_cursos:
        _, creado = EstadoEstudianteCurso.objects.update_or_create(
            nombre=estado['nombre'], defaults=estado
        )

        if creado:
            creados += 1

    print(f'{creados} estados estudiante-curso creados')

    # parsear datos
    estudiantes = {}

    for fila in archivo_estudiantes_cursos:
        if fila['model'] == 'app.alumno':
            pk = fila['pk']
            estudiantes[pk] = EstudianteTemp(fila)

        if fila['model'] == 'app.alumno_en_carrera':
            estudiantes[fila['fields']['alumno']].agregar_carrera(fila)

        if fila['model'] == 'app.alumno_en_curso':
            # omitir cursos eliminados por cuadratura
            if not fila['fields']['estado'] == 21:
                estudiantes[fila['fields']['alumno']].agregar_curso(fila)

    creados = 0
    for estudiante in estudiantes.values():
        estudiante.distribuir_cursos()

        for curso in estudiante.cursos:
            if curso.carrera and curso.instancia:
                try:
                    nota_final = None
                    if curso.nota_final and curso.nota_final != "0":
                        nota_final = curso.nota_final

                    _, creado = EstudianteCurso.objects.update_or_create(
                        estudiante=curso.carrera,
                        curso=curso.instancia,
                        defaults={
                            'estado': curso.estado,
                            'nota_final': nota_final,
                        }
                    )

                    if creado:
                        creados += 1

                except:
                    print(f'error procesando {curso.carrera} - {curso.instancia} (id {curso.pk})')
                    raise

    print(f'{creados} estudiante-curso registrados')
    return
