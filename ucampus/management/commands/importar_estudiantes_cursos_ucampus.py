from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

from ucampus.api import obtener_carreras_alumnos, obtener_todos_cursos_inscritos, obtener_cursos_inscritos, obtener_personas

from ucampus.management.commands.importar_docentes_ucampus import crear_persona_ucampus

from persona.permisos import GRUPOS

from academica.models import Plan
from persona.models import Persona, Estudiante, EstadoEstudiante
from curso.models import Curso, EstudianteCurso, EstadoEstudianteCurso, Periodo
from academica.models import Carrera


class Command(BaseCommand):
    def handle(self, *args, **options):
        importar_estudiantes_cursos_ucampus()
        return


class EstudianteCarreraTemp:
    def __init__(self, fila, persona):
        self.carrera = fila['id_carrera']
        self.carrera_nombre = fila['nombre']
        self.plan = fila['id_plan']

        try:
            self.periodo_inicio = Periodo.objects.get(id_ucampus=fila['periodo_inicio'])

            self.periodo_fin = None
            if fila['periodo_fin'] == '2018.3':
                fila['periodo_fin'] = '2018.2'
            if fila['periodo_fin']:
                self.periodo_fin = Periodo.objects.get(id_ucampus=fila['periodo_fin'])

        except Periodo.DoesNotExist:
            print(f"no existe un periodo con id {fila['periodo_inicio']}")

        self.instancia = None
        try:
            plan = Plan.objects.get(id_ucampus=self.plan)
            self.instancia, _ = Estudiante.objects.get_or_create(
                persona=persona, plan=plan,
                defaults={
                    'periodo_ingreso': self.periodo_inicio,
                    'estado_estudiante': EstadoEstudiante.objects.get(id_ucampus=fila['estado']),
                })

            if self.periodo_fin:
                self.instancia.periodo_egreso = self.periodo_fin
                self.instancia.save()

        except Estudiante.DoesNotExist:
            print(f'no existe el estudiante {persona.numero_documento} - {self.carrera_nombre}')
            raise

        except Estudiante.MultipleObjectsReturned:
            print(f'existe más de un estudiante {persona.numero_documento} - {self.carrera_nombre}')
            raise

    def __repr__(self):
        return (
            f'{self.instancia.plan.carrera.nombre} '
            f'{self.periodo_inicio.id_ucampus}-'
            f'{self.periodo_fin.id_ucampus if self.periodo_fin else "ahora"}'
        )


class EstudianteCursoTemp:
    def __init__(self, fila):
        self.id_curso = fila['id_curso']
        self.periodo = Periodo.objects.get(id_ucampus=fila['id_periodo'])

        try:
            self.estado = EstadoEstudianteCurso.objects.get(id_ucampus=fila['id_estado_final'])
        except EstadoEstudianteCurso.DoesNotExist:
            print(f'no existe un estado curso con id_ucampus {fila["id_estado_final"]}')
            raise

        self.nota_final = fila['nota_final']
        if self.nota_final == '':
            self.nota_final = None

        self.carrera = None

        self.instancia = None
        try:
            self.instancia = Curso.objects.get(id_ucampus=self.id_curso)
        except Curso.DoesNotExist:
            print(f'no existe un curso con id_ucampus {self.id_curso}')

    def __repr__(self):
        if self.instancia is None:
            return 'EstudianteCursoTemp error: '
        return f'{self.instancia.ramo}-{self.periodo.id_ucampus}'


class EstudianteTemp:
    def __init__(self, fila):
        self.rut = fila['rut']
        self.carreras = []
        self.cursos = []

        self.instancia = None
        try:
            self.instancia = Persona.objects.get(numero_documento=self.rut)
        except Persona.DoesNotExist:
            print(f'No existe una persona con rut {self.rut}')
            raise

    def agregar_carrera(self, fila_carrera):
        # solo agregar carreras existentes (ignorar licenciaturas)
        if Carrera.objects.filter(id_ucampus=fila_carrera['id_carrera']).exists():
            self.carreras.append(EstudianteCarreraTemp(fila_carrera, self.instancia))
            self.carreras.sort(key=lambda carrera: carrera.periodo_inicio)

    def agregar_curso(self, fila_curso):
        try:
            self.cursos.append(EstudianteCursoTemp(fila_curso))
        except Curso.MultipleObjectsReturned:
            print(f'existe más de un curso {fila_curso}')
            raise

    def distribuir_cursos(self):
        if len(self.carreras) == 0:
            return

        # solo es necesario chequear en estudiantes con más de una carrera
        if len(self.carreras) > 1:
            print(f'{self.rut} {self.carreras}')

            for curso in self.cursos:
                # omitir cursos que no existen en el sistema
                if not self.instancia:
                    continue

                carrera_curso = None
                multiple = False

                # chequear si el curso se encuentra dentro de los periodos de una carrera
                for carrera in self.carreras:
                    if carrera.periodo_inicio <= curso.periodo \
                            and (not carrera.periodo_fin or carrera.periodo_fin >= curso.periodo):

                        # chequear si es que hay colisión con otra carrera
                        if carrera_curso:
                            carrera_0 = self.carreras[0]

                            # periodo fin carrera anterior sobrepuesto con carrera actual
                            if carrera.periodo_inicio == curso.periodo \
                                    and (carrera_0.periodo_fin
                                         and carrera_0.periodo_fin == curso.periodo):
                                carrera_curso = carrera.instancia

                            else:
                                print(f'curso {curso} pertenece a más de una carrera')
                                tipo_carrera = carrera.instancia.plan.carrera.tipo_carrera
                                tipo_carrera_0 = carrera_0.instancia.plan.carrera.tipo_carrera

                                # si una carrera es pregrado y la otra no, preferir pregrado
                                if tipo_carrera == 0 and tipo_carrera_0 != 0:
                                    print(f'\ttomando carrera de pregrado {carrera}')
                                    carrera_curso = carrera.instancia

                                elif tipo_carrera != 0 and tipo_carrera_0 == 0:
                                    print(f'\ttomando carrera de pregrado {carrera_0}')
                                    carrera_curso = carrera.instancia

                                else:
                                    multiple = True

                        else:
                            carrera_curso = carrera.instancia

                if carrera_curso and not multiple:
                    curso.carrera = carrera_curso
                elif not carrera_curso:
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


def importar_estudiantes_cursos_ucampus():
    # crear estados curso estudiante
    creados = 0
    for estado in estados_cursos:
        _, creado = EstadoEstudianteCurso.objects.update_or_create(
            nombre=estado['nombre'], defaults=estado
        )

        if creado:
            creados += 1

    if creados:
        print(f'{creados} estados estudiante-curso creados')

    carreras_alumnos = obtener_carreras_alumnos()
    print(f'{len(carreras_alumnos)} registros de estudiantes obtenidos')

    ruts_existentes = Persona.objects.all().values_list('numero_documento', flat=True)
    ruts_estudiantes = [str(fila['rut']) for fila in carreras_alumnos]
    ruts_nuevos = [rut for rut in ruts_estudiantes if rut not in ruts_existentes]

    personas_nuevas = obtener_personas(ruts_nuevos)
    creados = 0
    for fila in personas_nuevas:
        crear_persona_ucampus(fila)
        creados += 1
    if creados:
        print(f'{creados} personas nuevas registradas\n')

    # asignar grupos
    grupo_estudiantes, _ = Group.objects.get_or_create(name=GRUPOS.ESTUDIANTES)
    for rut in ruts_estudiantes:
        usuario = User.objects.get(username=rut)
        usuario.groups.add(grupo_estudiantes)

    # parsear datos
    estudiantes = {}
    for fila in carreras_alumnos:
        if fila['rut'] not in estudiantes:
            estudiantes[fila['rut']] = EstudianteTemp(fila)

        estudiantes[fila['rut']].agregar_carrera(fila)

    cursos_inscritos = obtener_cursos_inscritos()
    # cursos_inscritos = obtener_todos_cursos_inscritos()
    print(f'{len(cursos_inscritos)} registros de estudiantes-cursos obtenidos')
    for fila in cursos_inscritos:
        try:
            estudiantes[fila['rut']].agregar_curso(fila)
        except KeyError:
            print(f"no se encontró estudiante con rut {fila['rut']} en api carreras_alumnos")
        except Curso.MultipleObjectsReturned:
            print(f"existe más de un curso {fila['rut']}")
            raise

    creados = 0
    actualizados = 0
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
                    else:
                        actualizados += 1

                except:
                    print(f'error procesando {curso.carrera} - {curso.instancia} (id {curso.pk})')
                    raise

    print(f'{creados} estudiante-curso registrados, {actualizados} actualizados')
    return
