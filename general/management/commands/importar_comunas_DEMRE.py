import csv

from django.core.management.base import BaseCommand
from general.models import Region, Provincia, Comuna


class Command(BaseCommand):
    help = 'Actualiza las regiones, provincias y comunas de acuerdo al archivo DEMRE'

    def add_arguments(self, parser):
        parser.add_argument('path_archivo', type=str)

    def handle(self, *args, **options):
        regiones = {}
        provincias = {}

        regiones_creadas = 0
        regiones_act = 0
        provincias_creadas = 0
        provincias_act = 0
        comunas_creadas = 0
        comunas_act = 0

        with open(options['path_archivo'], 'r', encoding='utf8') as archivo_comunas:
            data = csv.DictReader(archivo_comunas, delimiter=';')

            for fila in data:
                codigo_region = fila['REG_CODIGO']
                if codigo_region not in regiones:
                    region, creada = Region.objects.update_or_create(
                        codigo_demre=codigo_region,
                        defaults={
                            'nombre': fila['REG_NOMBRE'].title(),
                        })

                    regiones[codigo_region] = region

                    if creada:
                        regiones_creadas += 1
                    else:
                        regiones_act += 1

                codigo_provincia = fila['PRV_CODIGO_REFERENCIA']
                if codigo_provincia not in provincias:
                    provincia, creada = Provincia.objects.update_or_create(
                        codigo_demre=codigo_provincia,
                        defaults={
                            'nombre': fila['PRV_NOMBRE'].title(),
                            'region': regiones[codigo_region],
                        })

                    provincias[codigo_provincia] = provincia

                    if creada:
                        provincias_creadas += 1
                    else:
                        provincias_act += 1

                codigo_comuna = fila['COM_CODIGO_REFERENCIA']
                comuna, creada = Comuna.objects.update_or_create(
                    codigo_demre=codigo_comuna,
                    defaults={
                        'nombre': fila['COM_NOMBRE'].title(),
                        'region': regiones[codigo_region],
                        'provincia': provincias[codigo_provincia],
                    })

                if creada:
                    comunas_creadas += 1
                else:
                    comunas_act += 1

        print(f'{regiones_creadas} regiones creadas, {regiones_act} actualizadas')
        print(f'{provincias_creadas} provincias creadas, {provincias_act} actualizadas')
        print(f'{comunas_creadas} comunas creadas, {comunas_act} actualizadas')
        return
