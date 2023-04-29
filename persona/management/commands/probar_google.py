from django.core.management.base import BaseCommand

import httplib2
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp

from persona.models import Persona
from persona.google import obtener_mail_disponible, autenticar_server, obtener_unidad_organizativa


class Command(BaseCommand):
    def handle(self, *args, **options):
        print('autenticando al servidor')
        credentials = autenticar_server()
        api_google = build('admin', 'directory_v1', credentials=credentials)
        http = AuthorizedHttp(credentials=credentials, http=httplib2.Http())

        persona = Persona.objects.get(numero_documento=72459)
        print(f'buscando mail disponible para persona {persona}')

        mail_nuevo = obtener_mail_disponible(api_google, persona, http)
        print(f'mail obtenido: {mail_nuevo}')

        estudiante = persona.estudiantes.first()
        print('obteniendo unidad organizativa para', estudiante)
        obtener_unidad_organizativa(api_google, http, estudiante)
        return
