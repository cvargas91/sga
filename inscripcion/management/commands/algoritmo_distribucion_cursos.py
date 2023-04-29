from django.core.management.base import BaseCommand, CommandError
from inscripcion.models import ProcesoInscripcion
from inscripcion.algoritmos import distribucion_felicidad


class Command(BaseCommand):
    help = 'Ejecuta el algoritmo de distribucion de cursos en el proceso seleccionado'

    def add_arguments(self, parser):
        parser.add_argument('id_proceso', type=int)
        parser.add_argument('-a', '--algoritmo', default='felicidad', choices=['felicidad'])

    def handle(self, *args, **options):
        proceso = ProcesoInscripcion.objects.get(pk=options['id_proceso'])

        if options['algoritmo'] == 'felicidad':
            distribucion_felicidad(proceso)
        return
