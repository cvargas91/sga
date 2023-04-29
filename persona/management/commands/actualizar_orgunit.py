import time

from django.core.management.base import BaseCommand

import httplib2
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp

from persona.models import Estudiante
from persona.google import (
    autenticar_server, obtener_unidad_organizativa, actualizar_unidad_organizativa,
)


class Command(BaseCommand):
    help = """
        Actualiza la unidad organizativa (google) de todos los estudiantes de pregrado de los años
        ingresados.
    """

    def add_arguments(self, parser):
        parser.add_argument('año', type=int, nargs='+')

    def handle(self, *args, **options):
        print('autenticando al servidor')
        credentials = autenticar_server()
        api_google = build('admin', 'directory_v1', credentials=credentials)
        http = AuthorizedHttp(credentials=credentials, http=httplib2.Http())

        estudiantes = Estudiante.objects.filter(
            plan__carrera__tipo_carrera=0,  # solo carreras de pregrado, ignorar diplomados
            estado_estudiante=4,  # regular
            persona__mail_institucional__isnull=False,  # tiene mail institucional
            periodo_ingreso__ano__in=options['año'],
        )
        print(f'actualizando {estudiantes.count()} estudiantes')

        for estudiante in estudiantes:
            mail = estudiante.persona.mail_institucional

            # obtener unidad organizativa
            path_unidad = obtener_unidad_organizativa(api_google, http, estudiante)

            # actualizar unidad usuario
            print(f'asignando {mail} a {path_unidad}')
            actualizar_unidad_organizativa(api_google, http, mail, path_unidad)
            time.sleep(0.1)  # evitar sobrecargar la api
        return
