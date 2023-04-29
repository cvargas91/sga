from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import EnvioInscripcion, ProcesoInscripcion, SolicitudCurso
from curso.models import Curso, EstudianteCurso, Horario, Modulo, Periodo, EstadoEstudianteCurso
from academica.models import Departamento, Ramo, Carrera, Plan
from persona.models import Persona, Estudiante

from .algoritmos import distribucion_felicidad, traspasar_resultados_inscripcion


class InscripcionTestCase(TestCase):
    estudiantes = 100
    cursos = 6

    def setUp(self):

        # crear info académica
        depto = Departamento.objects.create(nombre='departamento')
        periodo = Periodo.objects.create(ano=1, numero=1, activo=True)

        for i in range(self.cursos):
            ramo = Ramo.objects.create(
                nombre=f'ramo-{i}', codigo=f'ramo-{i}', departamento=depto, creditos=5)
            Curso.objects.create(ramo=ramo, periodo=periodo, cupo=self.estudiantes, seccion=1)

        carrera = Carrera.objects.create(departamento=depto, nombre='carrera', tipo_carrera=0)
        plan = Plan.objects.create(carrera=carrera, version=1)

        EstadoEstudianteCurso.objects.update_or_create(
            nombre="Inscrito", defaults={"completado": False, "aprobado": False})

        # crear info usuario
        for i in range(self.estudiantes):
            user = User.objects.create(username=f'usuario-{i}')
            persona = Persona.objects.create(user=user, nombres=f'persona-{i}', numero_documento=i)
            Estudiante.objects.create(
                persona=persona, plan=plan, periodo_ingreso=periodo, estado_estudiante_id=4)

        # crear info inscripción académica
        ProcesoInscripcion.objects.create(
            nombre='proceso', periodo=periodo, tipo=1,
            fecha_apertura=timezone.now(), fecha_cierre=timezone.now())
        return

    def test_cupos_suficientes(self):
        proceso = ProcesoInscripcion.objects.first()
        cursos = Curso.objects.all()
        for persona in Persona.objects.all():
            envio = EnvioInscripcion.objects.create(persona=persona, proceso=proceso)

            for i in range(self.cursos):
                SolicitudCurso.objects.create(envio=envio, curso=cursos[i], prioridad=i, tipo=0)

        distribucion_felicidad(proceso)
        traspasar_resultados_inscripcion(proceso)

        for curso in Curso.objects.all():
            self.assertEqual(curso.estudiantes.count(), self.estudiantes)

        for persona in Persona.objects.all():
            cursos = EstudianteCurso.objects.filter(estudiante__persona=persona).count()
            self.assertEqual(cursos, self.cursos)

        return

    def test_cupos_insuficientes(self):
        # reducir cupo de todos los cursos a la mitad
        Curso.objects.update(cupo=self.estudiantes / 2)

        proceso = ProcesoInscripcion.objects.first()
        cursos = Curso.objects.all()
        for persona in Persona.objects.all():
            envio = EnvioInscripcion.objects.create(persona=persona, proceso=proceso)

            for i in range(self.cursos):
                SolicitudCurso.objects.create(envio=envio, curso=cursos[i], prioridad=i, tipo=0)

        distribucion_felicidad(proceso)
        traspasar_resultados_inscripcion(proceso)

        for curso in Curso.objects.all():
            self.assertEqual(curso.estudiantes.count(), self.estudiantes / 2)

        for persona in Persona.objects.all():
            cursos = EstudianteCurso.objects.filter(estudiante__persona=persona).count()
            self.assertEqual(cursos, self.cursos / 2)
        return

    def test_choque_horario(self):
        # crear choques de horario
        cursos = Curso.objects.all()
        modulo1 = Modulo.objects.create(hora_inicio=timezone.now(), hora_termino=timezone.now())
        modulo2 = Modulo.objects.create(hora_inicio=timezone.now(), hora_termino=timezone.now())

        # choque con 1 y 5
        Horario.objects.create(curso=cursos[0], modulo=modulo1, dia=1)
        Horario.objects.create(curso=cursos[0], modulo=modulo1, dia=3)
        Horario.objects.create(curso=cursos[0], modulo=modulo1, dia=5)

        # choque con 0 y 4
        Horario.objects.create(curso=cursos[1], modulo=modulo1, dia=2)
        Horario.objects.create(curso=cursos[1], modulo=modulo1, dia=5)

        # choque con 4
        Horario.objects.create(curso=cursos[2], modulo=modulo1, dia=4)
        Horario.objects.create(curso=cursos[2], modulo=modulo1, dia=6)

        Horario.objects.create(curso=cursos[3], modulo=modulo2, dia=1)
        Horario.objects.create(curso=cursos[3], modulo=modulo2, dia=3)

        # choque con 1 y 2
        Horario.objects.create(curso=cursos[4], modulo=modulo1, dia=2)
        Horario.objects.create(curso=cursos[4], modulo=modulo1, dia=4)

        # choque con 0
        Horario.objects.create(curso=cursos[5], modulo=modulo1, dia=3)
        Horario.objects.create(curso=cursos[5], modulo=modulo2, dia=5)

        proceso = ProcesoInscripcion.objects.first()

        # debería recibir 0, 2 y 3
        persona1 = Persona.objects.first()
        envio = EnvioInscripcion.objects.create(persona=persona1, proceso=proceso)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[0], prioridad=0, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[1], prioridad=1, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[2], prioridad=2, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[3], prioridad=3, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[4], prioridad=4, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[5], prioridad=5, tipo=0)

        # debería recibir 1, 2, 3 y 5
        persona2 = Persona.objects.all()[2]
        envio = EnvioInscripcion.objects.create(persona=persona2, proceso=proceso)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[0], prioridad=6, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[1], prioridad=1, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[2], prioridad=2, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[3], prioridad=3, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[4], prioridad=4, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=cursos[5], prioridad=5, tipo=0)

        distribucion_felicidad(proceso)
        traspasar_resultados_inscripcion(proceso)

        # cursos persona 1
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=cursos[0]).exists())

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=cursos[1]).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona1, curso=cursos[1]).estado, 3)

        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=cursos[2]).exists())
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=cursos[3]).exists())

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=cursos[4]).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona1, curso=cursos[4]).estado, 3)

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=cursos[5]).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona1, curso=cursos[5]).estado, 3)

        # cursos persona 2
        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=cursos[0]).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona2, curso=cursos[0]).estado, 3)

        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=cursos[1]).exists())
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=cursos[2]).exists())
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=cursos[3]).exists())

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=cursos[4]).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona2, curso=cursos[4]).estado, 3)

        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=cursos[5]).exists())
        return

    def test_limite_creditos(self):
        cursos = Curso.objects.all()
        curso0 = cursos[0]
        curso1 = cursos[1]
        curso2 = cursos[2]
        curso3 = cursos[3]
        curso4 = cursos[4]
        curso5 = cursos[5]

        # superar límite de créditos
        curso1.creditos = 10
        curso1.save()
        curso2.creditos = 8
        curso2.save()
        curso3.creditos = 8
        curso3.save()
        curso4.creditos = 6
        curso4.save()
        curso5.creditos = 3
        curso5.save()

        proceso = ProcesoInscripcion.objects.first()

        # debería recibir 0, 1, 2 y 4
        persona1 = Persona.objects.first()
        envio = EnvioInscripcion.objects.create(persona=persona1, proceso=proceso)
        SolicitudCurso.objects.create(envio=envio, curso=curso0, prioridad=0, tipo=0)  # 5
        SolicitudCurso.objects.create(envio=envio, curso=curso1, prioridad=1, tipo=0)  # 15
        SolicitudCurso.objects.create(envio=envio, curso=curso2, prioridad=2, tipo=0)  # 23
        SolicitudCurso.objects.create(envio=envio, curso=curso3, prioridad=3, tipo=0)  # 31 x
        SolicitudCurso.objects.create(envio=envio, curso=curso4, prioridad=4, tipo=0)  # 29
        SolicitudCurso.objects.create(envio=envio, curso=curso5, prioridad=5, tipo=0)  # 32 x

        # debería recibir 0, 2, 3, 4 y 5
        persona2 = Persona.objects.all()[2]
        envio = EnvioInscripcion.objects.create(persona=persona2, proceso=proceso)
        SolicitudCurso.objects.create(envio=envio, curso=curso0, prioridad=0, tipo=0)  # 5
        SolicitudCurso.objects.create(envio=envio, curso=curso2, prioridad=1, tipo=0)  # 13
        SolicitudCurso.objects.create(envio=envio, curso=curso3, prioridad=2, tipo=0)  # 21
        SolicitudCurso.objects.create(envio=envio, curso=curso4, prioridad=3, tipo=0)  # 27
        SolicitudCurso.objects.create(envio=envio, curso=curso1, prioridad=4, tipo=0)  # 37 x
        SolicitudCurso.objects.create(envio=envio, curso=curso5, prioridad=5, tipo=0)  # 30

        distribucion_felicidad(proceso)
        traspasar_resultados_inscripcion(proceso)

        # cursos persona 1
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=curso0).exists())
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=curso1).exists())
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=curso2).exists())

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=curso3).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona1, curso=curso3).estado, 4)

        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=curso4).exists())

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=curso5).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona1, curso=curso5).estado, 4)

        # cursos persona 2
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=curso0).exists())

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=curso1).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona2, curso=curso1).estado, 4)

        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=curso2).exists())
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=curso3).exists())
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=curso4).exists())
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=curso5).exists())
        return

    def test_curso_ya_inscrito(self):
        curso = Curso.objects.first()
        curso2 = Curso.objects.create(ramo=curso.ramo, periodo=curso.periodo, cupo=100, seccion=2)

        proceso = ProcesoInscripcion.objects.first()

        # debería recibir solo el primer curso
        persona1 = Persona.objects.first()
        envio = EnvioInscripcion.objects.create(persona=persona1, proceso=proceso)
        SolicitudCurso.objects.create(envio=envio, curso=curso, prioridad=0, tipo=0)
        SolicitudCurso.objects.create(envio=envio, curso=curso2, prioridad=1, tipo=0)

        # debería recibir solo el segundo curso
        persona2 = Persona.objects.all()[2]
        envio2 = EnvioInscripcion.objects.create(persona=persona2, proceso=proceso)
        SolicitudCurso.objects.create(envio=envio2, curso=curso2, prioridad=0, tipo=0)
        SolicitudCurso.objects.create(envio=envio2, curso=curso, prioridad=1, tipo=0)

        distribucion_felicidad(proceso)
        traspasar_resultados_inscripcion(proceso)

        # cursos persona 1
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=curso).exists())

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona1, curso=curso2).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona1, curso=curso2).estado, 5)

        # cursos persona 2
        self.assertTrue(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=curso2).exists())

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona2, curso=curso).exists())
        self.assertEqual(
            SolicitudCurso.objects.get(envio__persona=persona2, curso=curso).estado, 5)
        return

    def test_eliminar_curso(self):
        periodo = Periodo.objects.first()
        persona = Persona.objects.first()

        ramo = Ramo.objects.first()
        curso = Curso.objects.create(ramo=ramo, periodo=periodo, cupo=self.estudiantes, seccion=2)
        curso.creditos = 30
        curso.save()

        estado = EstadoEstudianteCurso.objects.get(nombre="Inscrito")
        EstudianteCurso.objects.create(
            curso=curso, estudiante=persona.estudiantes.first(), estado=estado)

        proceso = ProcesoInscripcion.objects.first()
        envio = EnvioInscripcion.objects.create(persona=persona, proceso=proceso)

        # eliminar curso ya inscrito
        SolicitudCurso.objects.create(envio=envio, curso=curso, prioridad=0, tipo=1)

        # agregar otros cursos
        cursos = Curso.objects.filter(seccion=1)
        for i in range(self.cursos):
            SolicitudCurso.objects.create(envio=envio, curso=cursos[i], prioridad=i, tipo=0)

        distribucion_felicidad(proceso)
        traspasar_resultados_inscripcion(proceso)

        for i in range(self.cursos):
            self.assertTrue(
                EstudianteCurso.objects.filter(
                    estudiante__persona=persona, curso=cursos[i]
                ).exists())

        self.assertFalse(
            EstudianteCurso.objects.filter(estudiante__persona=persona, curso=curso).exists())

        return
