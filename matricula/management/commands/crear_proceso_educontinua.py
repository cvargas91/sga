import csv
from datetime import datetime

from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand

import httplib2
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
from persona.google import autenticar_server, crear_unidad_organizativa

from academica.models import Departamento, Carrera, Plan
from matricula.models import (
    ProcesoMatricula, PeriodoProcesoMatricula, ValorMatricula, ValorArancel,
)
from pagos.models import CategoriasProductos, SubCategoriasProductos, Productos


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str)

    def handle(self, *args, **options):
        crear_proceso(options['archivo'])
        return


def crear_proceso(path_archivo: str):
    credentials = autenticar_server()
    api_google = build('admin', 'directory_v1', credentials=credentials)
    http = AuthorizedHttp(credentials=credentials, http=httplib2.Http())

    with open(path_archivo, 'r', encoding='utf8') as archivo:
        detalle_diplomados = csv.DictReader(archivo, delimiter=',')

        for detalle_diplomado in detalle_diplomados:
            ano = detalle_diplomado['año']
            proceso = ProcesoMatricula.objects.get(ano=ano)

            depto = Departamento.objects.get(nombre=detalle_diplomado['departamento'])
            carrera, _ = Carrera.objects.get_or_create(
                nombre=detalle_diplomado['nombre'],
                departamento=depto,
                tipo_carrera=1,  # diplomado
            )
            plan, _ = Plan.objects.get_or_create(carrera=carrera, version=1)

            fecha_inicio = make_aware(datetime.strptime(
                f"{detalle_diplomado['fecha_inicio']}-{detalle_diplomado['hora_inicio']}",
                '%d/%m/%Y-%H:%M:%S'
            ))
            fecha_fin = make_aware(datetime.strptime(
                f"{detalle_diplomado['fecha_fin']}-{detalle_diplomado['hora_fin']}",
                '%d/%m/%Y-%H:%M:%S'
            ))
            p, _ = PeriodoProcesoMatricula.objects.update_or_create(
                proceso_matricula=proceso,
                descripcion=detalle_diplomado['descripción_periodo'],
                defaults={
                    'publico': 2,  # educiacion continua
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                },
            )
            p.planes.set([plan])

            categoria = CategoriasProductos.objects.get(nombre=f'Matrícula {ano}')
            subcategoria_matricula = SubCategoriasProductos.objects.get(nombre='Matrícula')
            subcategoria_arancel = SubCategoriasProductos.objects.get(nombre='Arancel')

            valor_matricula = detalle_diplomado['valor_matricula']
            valor_arancel = detalle_diplomado['valor_arancel']

            producto_matricula, _ = Productos.objects.update_or_create(
                categoria=categoria,
                subcategoria=subcategoria_matricula,
                codigo_interno=plan.id,
                defaults=defaults_producto(ano, 'Matrícula', valor_matricula, plan),
            )
            ValorMatricula.objects.update_or_create(
                proceso_matricula=proceso,
                plan=plan,
                defaults={
                    'valor': valor_matricula,
                    'producto': producto_matricula,
                    'decreto': 'QWERTY12345',
                    'decreto_ano': proceso.ano,
                }
            )

            producto_arancel, _ = Productos.objects.update_or_create(
                categoria=categoria,
                subcategoria=subcategoria_arancel,
                codigo_interno=plan.id,
                defaults=defaults_producto(ano, 'Arancel', valor_arancel, plan),
            )
            ValorArancel.objects.update_or_create(
                proceso_matricula=proceso,
                plan=plan,
                defaults={
                    'valor': valor_arancel,
                    'producto': producto_arancel,
                    'decreto': 'QWERTY12345',
                    'decreto_ano': proceso.ano,
                }
            )

            crear_unidad_organizativa(
                api_google=api_google, http=http,
                unidad_padre='Alumnos Ed. Continua',
                ano=proceso.ano,
                carrera=plan.carrera.nombre,
                esperar=False,
            )
    return


def defaults_producto(ano, tipo, valor, plan):
    return {
        'nombre': f"{tipo} {ano} {plan}",
        'descripcion_corta': f"Valor {tipo} {ano} {plan}",
        'descripcion_larga': f"Valor {tipo} {ano} {plan}",
        'valor': valor,
        'observaciones_codigo_interno': 'plan_id',
        'marca': f"Matrícula {ano}",
        'stock': 1,
        'destacado': False,
        'numero_vistas': 0,
        'estado': True
    }
