from django.core.management.base import BaseCommand, CommandError
from inscripcion.models import ProcesoInscripcion
from inscripcion.algoritmos import traspasar_resultados_inscripcion


class Command(BaseCommand):
    help = '''Realiza el traspaso de información desde las solicitudes de un proceso a la tabla
     CursoEstudiante'''

    def add_arguments(self, parser):
        parser.add_argument('id_proceso', type=int)

    def handle(self, *args, **options):
        proceso = ProcesoInscripcion.objects.get(pk=options['id_proceso'])
        traspasar_resultados_inscripcion(proceso)
        return
