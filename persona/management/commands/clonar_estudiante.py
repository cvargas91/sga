from django.core.management.base import BaseCommand

from persona.models import Persona, Estudiante, HistorialEstadoEstudiante
from curso.models import EstudianteCurso


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('estudiante', type=str)
        parser.add_argument('persona', type=str)

    def handle(self, *args, **options):
        estudiante = Estudiante.objects.get(persona__numero_documento=options['estudiante'])
        persona = Persona.objects.get(numero_documento=options['persona'])

        EstudianteCurso.objects.filter(estudiante__persona=persona).delete()
        HistorialEstadoEstudiante.objects.filter(estudiante__persona=persona).delete()
        Estudiante.objects.filter(persona=persona).delete()

        estudiante_clon = Estudiante.objects.create(
            persona=persona,
            plan=estudiante.plan,
            estudiante_antiguo=estudiante.estudiante_antiguo,
            via_ingreso=estudiante.via_ingreso,
            periodo_ingreso=estudiante.periodo_ingreso,
            periodo_egreso=estudiante.periodo_egreso,
            periodo_ingreso_uaysen=estudiante.periodo_ingreso_uaysen,
            estado_estudiante=estudiante.estado_estudiante,
        )

        for curso in estudiante.cursos.all():
            EstudianteCurso.objects.create(
                estudiante=estudiante_clon,
                curso=curso.curso,
                estado=curso.estado,
                nota_final=curso.nota_final,
            )
        return
