import httplib2
import re
import secrets
import string
import time
import random
import unidecode

from django.conf import settings

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp


API_GOOGLE = None

SCOPES_USUARIOS = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.orgunit',
]

UNIDADES = None

ULTIMA_ACTUALIZACION_UNIDADES = 0


def autenticar_server(scope=SCOPES_USUARIOS):
    return service_account.Credentials.from_service_account_file(
        'config/cuenta_servicio.json', scopes=scope, subject=settings.GOOGLE_ADMIN_ACCOUNT,
    )


def normalizar_texto(texto):
    # reemplazar acentos por letra base y pasar a minúsculas
    texto = unidecode.unidecode(texto).lower()

    # quitar cualquier caracter especial restante (espacios, guiones, etc)
    return re.sub('[^A-Za-z0-9]+', '', texto)


def base_mail(persona):
    base = normalizar_texto(persona.nombres.split(' ')[0])

    if persona.apellido1:
        base = f'{base}.{normalizar_texto(persona.apellido1)}'

    return base


def obtener_mail_disponible(api_google, persona, http):
    base = base_mail(persona)

    usuarios = api_google.users().list(
        domain='alumnos.uaysen.cl',
        orderBy='email',
        query=f'email:{base}*',
        fields='users/emails',  # obtener solo los emails de los usuarios
    ).execute(http=http).get('users', [])

    if len(usuarios) == 0:
        return f'{base}@alumnos.uaysen.cl'

    # obtener todos los mails del dominio (incluyendo secundarios en caso de cambios)
    mails = set()
    for usuario in usuarios:
        for mail in usuario['emails']:
            if mail['address'].endswith('@alumnos.uaysen.cl'):
                mails.add(mail['address'])

    # buscar la primera opción que esté disponible
    i = 1
    while True:
        mail_nuevo = f'{base}{i}@alumnos.uaysen.cl'

        if mail_nuevo not in mails:
            break
        i += 1

    return mail_nuevo


def crear_mail_institucional(estudiante):
    if settings.DEBUG:
        return 'modo debug: no se creo la cuenta'

    persona = estudiante.persona

    # no recrear mails
    if persona.mail_institucional:
        return None

    # iniciar servicio solo una vez
    global API_GOOGLE
    if API_GOOGLE is None:
        API_GOOGLE = build('admin', 'directory_v1', credentials=autenticar_server())

    # crear una nueva instancia de http para cada request (thread safe)
    http = AuthorizedHttp(credentials=autenticar_server(), http=httplib2.Http())

    # obtener mail y contraseña
    mail_nuevo = obtener_mail_disponible(API_GOOGLE, persona, http)
    contrasena = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))

    # obtener unidad organizativa
    path_unidad = obtener_unidad_organizativa(API_GOOGLE, http, estudiante)

    # crear usuario
    usuario = {
        'name': {
            'familyName': persona.apellido1,
            'givenName': persona.nombres,
        },
        'primaryEmail': mail_nuevo,
        'password': contrasena,
        'changePasswordAtNextLogin': True,
        'externalIds': [
            {'value': persona.numero_documento, 'type': 'organization'}  # id del empleado
        ],
        'orgUnitPath': path_unidad,
    }
    API_GOOGLE.users().insert(body=usuario).execute(http=http)

    persona.mail_institucional = mail_nuevo
    persona.save()
    return contrasena


def unidad_organizativa(unidad_padre: str, ano: int = None, carrera: str = None):
    if ano is None:
        return {
            'name': unidad_padre,
            'description': unidad_padre,
            'parentOrgUnitPath': '/',
        }

    if carrera is None:
        return {
            'name': ano,
            'description': f'Cohorte {ano}',
            'parentOrgUnitPath': f'/{unidad_padre}',
        }

    return {
        'name': carrera,
        'description': f'{carrera} {ano}',
        'parentOrgUnitPath': f'/{unidad_padre}/{ano}',
    }


def path_unidad_organizativa(unidad_padre: str, ano: int = None, carrera: str = None):
    if ano is None:
        return f'/{unidad_padre}'

    if carrera is None:
        return f'/{unidad_padre}/{ano}'

    return f'/{unidad_padre}/{ano}/{carrera}'


def get_unidades(api_google, http):
    global UNIDADES, ULTIMA_ACTUALIZACION_UNIDADES

    # obtener unidades existentes solo 1 vez cada 5 minutos
    if UNIDADES is None or time.time() - ULTIMA_ACTUALIZACION_UNIDADES > 300:
        unidades = api_google.orgunits().list(
            customerId='my_customer',
            type='all',  # obtener todos las subunidades
            fields='organizationUnits/orgUnitPath',  # obtener solo los paths
        ).execute(http=http).get('organizationUnits', [])

        UNIDADES = [unidad['orgUnitPath'] for unidad in unidades]
        ULTIMA_ACTUALIZACION_UNIDADES = time.time()

    return UNIDADES


def obtener_unidad_organizativa(api_google, http, estudiante):
    ano = estudiante.periodo_ingreso.ano
    carrera = estudiante.plan.carrera.nombre
    unidad_padre = estudiante.unidad_organizativa()
    path_unidad = path_unidad_organizativa(unidad_padre=unidad_padre, ano=ano, carrera=carrera)

    # buscar unidad existente
    if path_unidad not in get_unidades(api_google, http):
        # crear nueva unidad y actualizar unidades registradas
        crear_unidad_organizativa(
            api_google=api_google, http=http, unidad_padre=unidad_padre, ano=ano, carrera=carrera)

    return path_unidad


def crear_unidad_organizativa(api_google, http, unidad_padre, ano=None, carrera=None, esperar=True):
    unidad = unidad_organizativa(unidad_padre=unidad_padre, ano=ano, carrera=carrera)
    path_unidad = path_unidad_organizativa(unidad_padre=unidad_padre, ano=ano, carrera=carrera)

    unidades = get_unidades(api_google, http)
    if path_unidad in unidades:
        return

    if unidad['parentOrgUnitPath'] not in unidades:
        if carrera is None:
            crear_unidad_organizativa(
                api_google=api_google,
                http=http,
                unidad_padre=unidad_padre,
                ano=None,
                carrera=None,
                esperar=esperar,
            )

        else:
            crear_unidad_organizativa(
                api_google=api_google,
                http=http,
                unidad_padre=unidad_padre,
                ano=ano,
                carrera=None,
                esperar=esperar,
            )

    print(f'creando unidad {path_unidad}')
    api_google.orgunits().insert(
        customerId='my_customer',
        body=unidad,
    ).execute(http=http)
    time.sleep(1)  # evitar pasar el límite de gapi (1 unidad por segundo)

    global UNIDADES
    UNIDADES.append(path_unidad)

    # al crear una unidad organizativa no está disponible para ser asignada inmediatamente
    if esperar:
        time.sleep(60)
    return


def actualizar_unidad_organizativa(api_google, http, mail, path_unidad, intento=0):
    try:
        api_google.users().update(
            userKey=mail, body={'orgUnitPath': path_unidad},
        ).execute(http=http)

    except Exception as e:
        if e.status_code == 404:
            print(f'no se ha encontrado al usuario con correo {mail}')
            return

        elif e.status_code != 403:
            raise

        if intento > 5:
            raise

        # exponential backoff
        time.sleep(2**intento + random.randrange(1, 1000) / 1000)
        actualizar_unidad_organizativa(api_google, http, mail, path_unidad, intento + 1)

    return
