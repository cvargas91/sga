import csv

from django.core.management.base import BaseCommand
from general.models import Pais


class Command(BaseCommand):
    help = 'Actualiza los paises de acuerdo al archivo mineduc'

    def add_arguments(self, parser):
        parser.add_argument('path_archivo', type=str)

    def handle(self, *args, **options):
        paises_creados = 0
        paises_act = 0

        with open(options['path_archivo'], 'r', encoding='utf8') as archivo:
            data = csv.DictReader(archivo, delimiter=';')

            for fila in data:
                pais, creado = Pais.objects.update_or_create(
                    codigo_mineduc=fila['numeroPais_MINEDUC'],
                    defaults={
                        'nombre': fila['nombrePais'].title(),
                    })

                if creado:
                    paises_creados += 1
                else:
                    paises_act += 1

        print(f'{paises_creados} paises creados, {paises_act} actualizadas')
        return
