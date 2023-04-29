from django.core.management.base import BaseCommand

import httplib2
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp

from persona.models import Persona
from persona.google import autenticar_server


class Command(BaseCommand):
    help = '''Setea el año de ingreso uaysen para todos los estudiantes actuales'''

    def handle(self, *args, **options):
        api_google = build('admin', 'directory_v1', credentials=autenticar_server())
        http = AuthorizedHttp(credentials=autenticar_server(), http=httplib2.Http())

        usuarios = []

        # obtener todos los usuarios
        nextPageToken = None
        while True:
            res = obtener_usuarios(api_google, http, nextPageToken)
            usuarios.extend(res.get('users', []))

            nextPageToken = res.get('nextPageToken', False)
            if not nextPageToken:
                break

        print(f'{len(usuarios)} usuarios encontrados')
        no_encontrados = 0
        actualizados = 0
        for user in usuarios:

            try:
                persona = Persona.objects.get(mail_institucional=user['primaryEmail'])

                # omitir usuarios que ya tienen externalIds definidos
                if 'externalIds' in user:
                    continue

                body = {
                    'externalIds': [
                        {'value': persona.numero_documento, 'type': 'organization'}
                    ]
                }
                api_google.users().update(
                    userKey=persona.mail_institucional, body=body
                ).execute(http=http)
                actualizados += 1

            except Persona.DoesNotExist:
                no_encontrados += 1
                # print(f'no se encontró una persona con mail {user["primaryEmail"]}')

        print(f'{actualizados} usuarios acualizados, ')
        print(f'{no_encontrados} no fueron encontrados')
        return


def obtener_usuarios(api_google, http, pageToken=None):
    return api_google.users().list(
        domain='alumnos.uaysen.cl',
        orderBy='email',
        fields='users/primaryEmail,users/externalIds,nextPageToken',
        maxResults=500,
        pageToken=pageToken,
    ).execute(http=http)
