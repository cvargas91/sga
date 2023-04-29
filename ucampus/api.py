import requests
from typing import List

from django.conf import settings

from curso.models import Periodo


def consultar_api(api: str, params={}):
    result = requests.get(
        f'{settings.UCAMPUS_API}/{api}', params=params,
        auth=(settings.UCAMPUS_USER, settings.UCAMPUS_PASS)
    )

    if result.status_code != 200:
        raise Exception(
            f'ha habido un error al intentar consultar {settings.UCAMPUS_API}/{api}\n'
            f'\tparams: {params}\n\n'
            f'error {result.status_code}: {result.text}'
        )

    return result.json()


TIPOS_CARRERAS_UCAMPUS = {
    2: 0,  # pregrado
    6: 1,  # diplomado
    7: 2,  # curso de especialización
}


# https://ucampus.uaysen.cl/api/0/mufasa/carreras.h?tipo_titulo[]=2&tipo_titulo[]=6&tipo_titulo[]=7
def obtener_carreras(tipo_titulo: List[int] = (2, 6, 7)):
    return consultar_api(api='carreras.json', params={'tipo_titulo[]': tipo_titulo})


# https://ucampus.uaysen.cl/api/0/mufasa/planes
def obtener_planes():
    return consultar_api(api='planes.json')


# https://ucampus.uaysen.cl/api/0/mufasa/cursos?periodo[]=2017.1&periodo[]=2017.2
def obtener_cursos(periodos: List[int] = ()):
    return consultar_api(api='cursos.json', params={'periodo[]': periodos})


def obtener_todos_cursos():
    cursos = []
    for periodo in Periodo.objects.all():
        cursos.extend(obtener_cursos(periodos=[periodo.id_ucampus]))
    return cursos


# https://ucampus.uaysen.cl/api/0/mufasa/ramos
def obtener_ramos():
    return consultar_api(api='ramos.json')


# https://ucampus.uaysen.cl/api/0/mufasa/cursos_dictados
def obtener_cursos_dictados(periodos: List[int] = ()):
    return consultar_api(api='cursos_dictados.json', params={'periodo[]': periodos})


def obtener_todos_cursos_dictados():
    cursos_dictados = []
    for periodo in Periodo.objects.all():
        cursos_dictados.extend(obtener_cursos_dictados(periodos=[periodo.id_ucampus]))
    return cursos_dictados


# https://ucampus.uaysen.cl/api/0/mufasa/horarios
def obtener_horarios(periodos: List[int] = ()):
    return consultar_api(api='horarios.json', params={'periodo[]': periodos})


def obtener_todos_horarios():
    horarios = []
    for periodo in Periodo.objects.all():
        horarios.extend(obtener_horarios(periodos=[periodo.id_ucampus]))
    return horarios


# https://ucampus.uaysen.cl/api/0/mufasa/personas
def obtener_personas(ruts: List[int] = (), max_ruts=200):
    # se debe dividir la consulta si hay demasiados ruts
    if len(ruts) > max_ruts:
        personas = obtener_personas(ruts[:max_ruts])
        personas.extend(obtener_personas(ruts[max_ruts:]))
        return personas

    return consultar_api(api='personas.json', params={'rut[]': ruts})


# https://ucampus.uaysen.cl/api/0/mufasa/carreras_alumnos
def obtener_carreras_alumnos():
    return consultar_api(api='carreras_alumnos.json')


# https://ucampus.uaysen.cl/api/0/mufasa/cursos_inscritos
def obtener_cursos_inscritos(periodo: str = None):
    return consultar_api(api='cursos_inscritos.json', params={'periodo': periodo})

def obtener_todos_cursos_inscritos():
    cursos_inscritos = []
    for periodo in Periodo.objects.all():
        cursos_inscritos.extend(obtener_cursos_inscritos(periodo.id_ucampus))
    return cursos_inscritos