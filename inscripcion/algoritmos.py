import random

from django.db.models import Max, Min
from academica.models import MallaObligatoria

from curso.models import Curso, CursosCompartidos, EstudianteCurso, EstadoEstudianteCurso, Periodo
from .models import (
    EnvioInscripcion, SolicitudCurso,
)


LIMITE_CREDITOS = 30


class EstudianteTemp:

    def __init__(self, persona, periodo):
        self.id = persona
        self.felicidad = 0
        self.ramos = []
        self.creditos = 0
        self.horario = set()

        cursos_incritos = EstudianteCurso.objects.filter(
            estudiante__persona=persona, curso__periodo=periodo).select_related('curso')
        for curso_inscrito in cursos_incritos:
            curso = curso_inscrito.curso

            self.creditos += curso.creditos
            self.ramos.append(curso.ramo_id)

            for bloque in curso.horario.all():
                self.horario.add(bloque.id_bloque())

    def __repr__(self):
        return f'felicidad: {self.felicidad} - ramos: {self.ramos}  '\
            f'{self.creditos} creditos - horario: {self.horario}'


class CursoTemp:

    def __init__(self, curso):
        self.id = curso.id
        self.id_ramo = curso.ramo_id
        self.cupos = curso.cupo
        self.ocupados = curso.estudiantes.count()
        self.creditos = curso.creditos

        self.horario = set()
        for bloque in curso.horario.all():
            self.horario.add(bloque.id_bloque())

    def disponibles(self):
        return self.cupos - self.ocupados

    def __repr__(self):
        return f'cupos: {self.ocupados}/{self.cupos} - '\
            f'{self.creditos} creditos - horario: {self.horario}'


def distribucion_felicidad(proceso, verbose=False):
    # cargar datos de cursos
    cursos = {}
    for curso in Curso.objects.filter(periodo=proceso.periodo):
        cursos[curso.id] = CursoTemp(curso)

    # cargar datos de estudiantes
    estudiantes = {}
    ids_persona = EnvioInscripcion.objects.filter(proceso=proceso).values_list('persona', flat=True)
    for id_persona in ids_persona:
        estudiantes[id_persona] = EstudianteTemp(id_persona, proceso.periodo)

    # procesar solicitudes de eliminación
    eliminaciones = SolicitudCurso.objects.filter(envio__proceso=proceso, tipo=1) \
        .select_related('envio__persona').select_related('curso')
    for solicitud in eliminaciones:
        solicitud.estado = 1
        solicitud.save()

        # actualizar cupos CursoTemp
        curso = cursos[solicitud.curso_id]
        curso.ocupados -= 1

        # actualizar EstudianteTemp
        estudiante = estudiantes[solicitud.envio.persona_id]
        estudiante.ramos.remove(solicitud.curso.ramo_id)
        estudiante.creditos -= curso.creditos
        estudiante.horario.difference_update(curso.horario)

    # procesar solicitudes de agregar
    solicitudes = SolicitudCurso.objects.filter(envio__proceso=proceso, tipo=0) \
        .select_related('envio__persona')

    # obtener rango de prioridades
    min_max = solicitudes.aggregate(min=Min('prioridad'), max=Max('prioridad'))
    min_prioridad = min_max['min']
    max_prioridad = min_max['max']

    # ordenar solicitudes por prioridad -> curso -> solicitudes
    solicitudes_ordenadas = []

    for prioridad in range(min_prioridad, max_prioridad + 1):
        solicitudes_cursos = {}
        solicitudes_prioridad = solicitudes.filter(prioridad=prioridad)

        # ordenar solicitudes por curso
        cursos_solicitados = solicitudes_prioridad.values_list('curso', flat=True).distinct()
        for curso in cursos_solicitados:
            solicitudes_cursos[curso] = solicitudes_prioridad.filter(curso=curso)

        solicitudes_ordenadas.append(solicitudes_cursos)

    # recorrer solicitudes según prioridad
    for solicitudes_cursos in solicitudes_ordenadas:
        for id_curso in solicitudes_cursos:
            curso = cursos[id_curso]

            # validar solicitudes
            validas = []
            for solicitud in solicitudes_cursos[id_curso]:
                estudiante = estudiantes[solicitud.envio.persona_id]

                # curso ya inscrito
                if curso.id_ramo in estudiante.ramos:
                    solicitud.estado = 5
                    solicitud.save()

                # límite de créditos
                elif estudiante.creditos + curso.creditos > LIMITE_CREDITOS:
                    solicitud.estado = 4
                    solicitud.save()

                # choque de horario
                elif not estudiante.horario.isdisjoint(curso.horario):
                    solicitud.estado = 3
                    solicitud.save()

                else:
                    validas.append(solicitud)

            # aleotorizar orden de ids y ordenar por felicidad
            random.shuffle(validas)
            validas.sort(key=lambda sol: estudiantes[sol.envio.persona_id].felicidad)

            # distribuir cupos
            disponibles = curso.disponibles()
            for solicitud in validas[:disponibles]:
                solicitud.estado = 1
                solicitud.save()

                curso.ocupados += 1

                estudiante = estudiantes[solicitud.envio.persona_id]
                estudiante.felicidad += 1
                estudiante.ramos.append(curso.id_ramo)
                estudiante.creditos += curso.creditos
                estudiante.horario.update(curso.horario)

            # actualizar rechazados
            for solicitud in validas[disponibles:]:
                solicitud.estado = 2
                solicitud.save()

                estudiantes[solicitud.envio.persona_id].felicidad -= 1

    for persona_id in estudiantes:
        envio = EnvioInscripcion.objects.get(persona__id=persona_id, proceso=proceso)
        envio.felicidad = estudiantes[persona_id].felicidad
        envio.save()

    if verbose:
        # imprimir resumen de solicitudes y estudiantes
        for solicitud in SolicitudCurso.objects.filter(envio__proceso=proceso):
            print(solicitud)

        print('\n')
        for id_persona in estudiantes:
            print(estudiantes[id_persona])

        print('\n')
        for id_curso in cursos:
            print(cursos[id_curso])

    return


def traspasar_resultados_inscripcion(proceso):
    # obtener todas las solicitudes aceptadas
    solicitudes = SolicitudCurso.objects.filter(envio__proceso=proceso, estado=1) \
        .select_related('envio__persona').select_related('curso')

    estado_inscrito = EstadoEstudianteCurso.objects.get(nombre="Inscrito")

    for solicitud in solicitudes:
        persona = solicitud.envio.persona
        curso = solicitud.curso

        # agregar
        if solicitud.tipo == 0:
            nuevo = EstudianteCurso(
                estudiante=persona.estudiante_activo(),
                curso=curso,
                estado=estado_inscrito,
            )
            nuevo.save()

        # eliminar
        elif solicitud.tipo == 1:
            antiguo = EstudianteCurso.objects.get(
                estudiante=persona.estudiante_activo(),
                curso=curso,
            )
            antiguo.delete()

    return


def inscribir_asignaturas_primer_semestre(estudiante):

    periodo_actual = Periodo.get_activo()

    malla = MallaObligatoria.objects.filter(plan=estudiante.plan, semestre=1)
    lista_ids_ramos = list(malla.values_list('ramo', flat=True))

    cursos_compartidos = CursosCompartidos.objects.filter(
        ramo__in=lista_ids_ramos, plan=estudiante.plan)

    for id in lista_ids_ramos:
        if cursos_compartidos.filter(ramo=id).exists():
            print(f'el curso {id} es compartido, buscar seccion')

            curso_compartido = cursos_compartidos.get(
                plan=estudiante.plan, ramo=id)

            seccion = curso_compartido.seccion
            print(f'la seccion que corresponde al estudiante es la numero {seccion}')

            curso = Curso.objects.get(
                ramo=curso_compartido.ramo, seccion=seccion, periodo=periodo_actual)

            print(f'inscribiendo curso {curso}')
            EstudianteCurso.objects.update_or_create(
                estudiante=estudiante,
                curso=curso,
                estado=EstadoEstudianteCurso.objects.get(nombre="Inscrito"))

        else:
            print(f"el curso {id} no es compartido, inscripción normal")

            curso = Curso.objects.filter(ramo=id, periodo=periodo_actual)

            if curso.count() > 1:  # hay mas de una sección disponible, probar en orden
                for c in curso:
                    if (c.cupo > c.estudiantes.count()):
                        curso = c
                        break
            else:
                curso = curso.first()  # convertir queryset de 1 en instancia Curso

            print(f'inscribiendo curso {curso}')
            EstudianteCurso.objects.update_or_create(
                estudiante=estudiante,
                curso=curso,
                estado=EstadoEstudianteCurso.objects.get(nombre="Inscrito"))

    return
