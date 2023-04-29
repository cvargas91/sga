from django.core.management.base import BaseCommand

from persona.models import Persona


class Command(BaseCommand):
    help = '''Setea el año de ingreso uaysen para todos los estudiantes actuales'''

    def handle(self, *args, **options):
        print('iniciando proceso...')
        personas = Persona.objects.all()
        actualizados = 0

        for persona in personas:
            periodo_ingreso_uaysen = persona.periodo_ingreso_uaysen()

            if periodo_ingreso_uaysen is not None:
                persona.estudiantes.update(periodo_ingreso_uaysen=periodo_ingreso_uaysen)
                actualizados += 1

        print(f'{actualizados} personas actualizadas')
        return
