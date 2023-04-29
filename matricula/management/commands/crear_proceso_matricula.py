from datetime import datetime

from django.utils.timezone import make_aware
from django.core.management.base import BaseCommand

import httplib2
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
from persona.google import autenticar_server, crear_unidad_organizativa

from academica.models import Plan
from curso.models import Periodo
from matricula.models import (
    ProcesoMatricula, PeriodoProcesoMatricula, ValorMatricula, ValorArancel,
)
from pagare.models import ModalidadCuotaPagare
from pagos.models import CategoriasProductos, SubCategoriasProductos, Productos


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--limpiar-datos', action='store_true')

    def handle(self, *args, **options):
        crear_proceso()
        return


periodos = [
    {
        'id': 19,
        'ano': 2021,
        'numero': 2,
        'activo': False,
    },
    {
        'id': 20,
        'ano': 2022,
        'numero': 1,
        'activo': False,
    },
    {
        'id': 21,
        'ano': 2023,
        'numero': 1,
        'activo': True,
    },
]

proceso_matricula = {
    'ano': 2023,
    'fecha_vigencia': make_aware(datetime(2024, 2, 1)),
    'activo': True
}

periodos_procesos = [
    {
        'descripcion': 'primer periodo estudiantes nuevos',
        'publico': 0,

        'fecha_inicio': make_aware(datetime(2023, 1, 18,  0)),
        'fecha_fin':    make_aware(datetime(2023, 1, 20, 18)),

        'dcto_oportuno': 5,
        'fecha_entrega_pagare': make_aware(datetime(2023, 3, 30)),
        'fecha_pago_matricula': make_aware(datetime(2022, 1, 18)),
        'fecha_pago_arancel': make_aware(datetime(2022, 1, 18)),
    },
    {
        'descripcion': 'segundo periodo estudiantes nuevos',
        'publico': 0,

        'fecha_inicio': make_aware(datetime(2023, 1, 21,  9)),
        'fecha_fin':    make_aware(datetime(2023, 1,  27, 23, 59)),

        'dcto_oportuno': 5,
        'fecha_entrega_pagare': make_aware(datetime(2022, 3, 30)),
        'fecha_pago_matricula': make_aware(datetime(2023, 1, 27)),
        'fecha_pago_arancel': make_aware(datetime(2023, 1, 27)),
    },
    {
        'descripcion': 'primer periodo estudiantes antiguos',
        'publico': 1,

        'fecha_inicio': make_aware(datetime(2023, 1, 24,  9)),
        'fecha_fin':    make_aware(datetime(2023, 1, 25, 23, 59)),

        'dcto_oportuno': 5,
        'fecha_entrega_pagare': make_aware(datetime(2023, 3, 30)),
        'fecha_pago_matricula': make_aware(datetime(2023, 1, 25)),
        'fecha_pago_arancel': make_aware(datetime(2023, 1, 25)),
    },
    {
        'descripcion': 'segundo periodo estudiantes antiguos',
        'publico': 1,

        'fecha_inicio': make_aware(datetime(2023, 2, 28,  9)),
        'fecha_fin':    make_aware(datetime(2023, 3, 1, 23, 59)),

        'dcto_oportuno': 5,
        'fecha_entrega_pagare': make_aware(datetime(2023, 3, 30)),
        'fecha_pago_matricula': make_aware(datetime(2023, 3, 1)),
        'fecha_pago_arancel': make_aware(datetime(2023, 3, 1)),
    },
    {
        'descripcion': 'periodo rezagados estudiantes antiguos',
        'publico': 1,

        'fecha_inicio': make_aware(datetime(2023, 3, 9,  0)),
        'fecha_fin':    make_aware(datetime(2023, 3, 9, 23, 59)),

        'dcto_oportuno': 5,
        'fecha_entrega_pagare': make_aware(datetime(2023, 3, 30)),
        'fecha_pago_matricula': make_aware(datetime(2023, 3, 9)),
        'fecha_pago_arancel': make_aware(datetime(2023, 3, 9)),
    },
]

detalles_planes = [
    {
        'plan': 1,  # Enfermería
        'valor_matricula': 130000,
        'valor_arancel': 3285776,
        'pagare_nuevos': '1t2qTHqu-ji0eAXCDSBEcMNHLlvvUCY5t',
        'pagare_antiguos': '1t2qTHqu-ji0eAXCDSBEcMNHLlvvUCY5t',
    },
    {
        'plan': 2,  # Obstetricia
        'valor_matricula': 130000,
        'valor_arancel': 3285776,
        'pagare_nuevos': '1tNngKZvVpCCXX9bFcB4kdFKkNHx1JSx9',
        'pagare_antiguos': '1tNngKZvVpCCXX9bFcB4kdFKkNHx1JSx9',
    },
    {
        'plan': 3,  # Agronomía
        'valor_matricula': 130000,
        'valor_arancel': 3390948,
        'pagare_nuevos': '1hW2HMfaokh5yayEsgR8lsF--Bmj26lF4',
        'pagare_antiguos': '1hW2HMfaokh5yayEsgR8lsF--Bmj26lF4',
    },
    {
        'plan': 4,  # Ingeniería Forestal
        'valor_matricula': 130000,
        'valor_arancel': 3390948,
        'pagare_nuevos': '1qFUEO8HyDRcedSyv4eysX5Rn3vmXckW-',
        'pagare_antiguos': '1qFUEO8HyDRcedSyv4eysX5Rn3vmXckW-',
    },
    {
        'plan': 5,  # Ingeniería Civil Industrial
        'valor_matricula': 130000,
        'valor_arancel': 3415089,
        'pagare_nuevos': '1qS5LNhiHx9bTfloK8SvuNFFfFMluYKD6',
        'pagare_antiguos': '1qS5LNhiHx9bTfloK8SvuNFFfFMluYKD6',
    },
    {
        'plan': 6,  # Trabajo Social
        'valor_matricula': 130000,
        'valor_arancel': 2458175,
        'pagare_nuevos': '10doQ9Z9N3dzbYzBHT08_xJ5_dACNi5iI',
        'pagare_antiguos': '10doQ9Z9N3dzbYzBHT08_xJ5_dACNi5iI',
    },
    {
        'plan': 7,  # Psicología
        'valor_matricula': 130000,
        'valor_arancel': 3285776,
        'pagare_nuevos': '1FCEsLDw367h0GxFG8qGsj4u82Ux2SsDh',
        'pagare_antiguos': '1FCEsLDw367h0GxFG8qGsj4u82Ux2SsDh',
    },
    {
        'plan': 8,  # Ingeniería Civil Informática
        'valor_matricula': 130000,
        'valor_arancel':  3415089,
        'pagare_nuevos': '1scpjrjnHdwgjc8Ya-oSQyYjLMyh4BgQv',
        'pagare_antiguos': '1scpjrjnHdwgjc8Ya-oSQyYjLMyh4BgQv',
    },
]

cantidad_cuotas = 10
fecha_primera_cuota = '25 de marzo'


def defaults_producto(tipo, valor, plan):
    return {
        'nombre': f"{tipo} {proceso_matricula['ano']} {plan}",
        'descripcion_corta': f"Valor {tipo} {proceso_matricula['ano']} {plan}",
        'descripcion_larga': f"Valor {tipo} {proceso_matricula['ano']} {plan}",
        'valor': valor,
        'observaciones_codigo_interno': 'plan_id',
        'marca': f"Matrícula {proceso_matricula['ano']}",
        'stock': 1,
        'destacado': False,
        'numero_vistas': 0,
        'estado': True
    }


def defaults_valor_matricula(valor, producto):
    return {
        'valor': valor,
        'producto': producto,
        'decreto': 'QWERTY12345',
        'decreto_ano': 2023,
    }


def defaults_valor_arancel(valor, producto):
    return {
        'valor': valor,
        'producto': producto,
        'decreto': 'ASDFG12345',
        'decreto_ano': 2023,
    }


def crear_proceso():
    for periodo in periodos:
        Periodo.objects.get_or_create(
            id=periodo['id'],
            ano=periodo['ano'],
            numero=periodo['numero'],
            defaults=periodo)

    proceso, _ = ProcesoMatricula.objects.update_or_create(
        ano=proceso_matricula['ano'],
        defaults={
            **proceso_matricula,
            'periodo_ingreso': Periodo.objects.get_by_natural_key(proceso_matricula['ano'], 1),
        }
    )

    for periodo in periodos_procesos:
        p, _ = PeriodoProcesoMatricula.objects.update_or_create(
            proceso_matricula=proceso,
            descripcion=periodo['descripcion'],
            defaults=periodo,
        )
        p.planes.set(Plan.objects.filter(carrera__tipo_carrera=0))  # pregrado

    categoria, _ = CategoriasProductos.objects.get_or_create(
        nombre=f"Matrícula {proceso_matricula['ano']}", defaults={'estado': True},
    )
    subcategoria_matricula = SubCategoriasProductos.objects.get(nombre='Matrícula')
    subcategoria_arancel = SubCategoriasProductos.objects.get(nombre='Arancel')

    credentials = autenticar_server()
    api_google = build('admin', 'directory_v1', credentials=credentials)
    http = AuthorizedHttp(credentials=credentials, http=httplib2.Http())

    for detalles_plan in detalles_planes:
        plan = Plan.objects.get(id=detalles_plan['plan'])
        valor_matricula = detalles_plan['valor_matricula']
        valor_arancel = detalles_plan['valor_arancel']

        producto_matricula, _ = Productos.objects.update_or_create(
            categoria=categoria,
            subcategoria=subcategoria_matricula,
            codigo_interno=plan.id,
            defaults=defaults_producto('Matrícula', valor_matricula, plan),
        )
        ValorMatricula.objects.update_or_create(
            proceso_matricula=proceso,
            plan=plan,
            defaults=defaults_valor_matricula(valor_matricula, producto_matricula)
        )

        producto_arancel, _ = Productos.objects.update_or_create(
            categoria=categoria,
            subcategoria=subcategoria_arancel,
            codigo_interno=plan.id,
            defaults=defaults_producto('Arancel', valor_arancel, plan),
        )
        ValorArancel.objects.update_or_create(
            proceso_matricula=proceso,
            plan=plan,
            defaults=defaults_valor_arancel(valor_arancel, producto_arancel)
        )

        ModalidadCuotaPagare.objects.update_or_create(
            proceso_matricula=proceso,
            plan=plan,
            cantidad_cuotas=cantidad_cuotas,
            curso_asociado=0,
            defaults={
                'fecha_primera_cuota': fecha_primera_cuota,
                'link_pagare': detalles_plan['pagare_nuevos'],
            },
        )
        ModalidadCuotaPagare.objects.update_or_create(
            proceso_matricula=proceso,
            plan=plan,
            cantidad_cuotas=cantidad_cuotas,
            curso_asociado=1,
            defaults={
                'fecha_primera_cuota': fecha_primera_cuota,
                'link_pagare': detalles_plan['pagare_antiguos'],
            },
        )

        # crear unidad organizativa en google admin
        crear_unidad_organizativa(
            api_google=api_google, http=http,
            unidad_padre='Alumnos',
            ano=proceso_matricula['ano'],
            carrera=plan.carrera.nombre,
            esperar=False,
        )
    return
