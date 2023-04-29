import httplib2
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
from persona.google import (
    autenticar_server, obtener_unidad_organizativa, actualizar_unidad_organizativa,
)

from academica.models import Plan
from curso.models import EstudianteCurso
from persona.models import Estudiante
from .models import Solicitud


def aprobar_postergacion(instance, estado_anterior):

    instance.estudiante.estado_estudiante_id = 1
    instance.estudiante.save()

    cursos_actuales = EstudianteCurso.objects.filter(
        estudiante=instance.estudiante,
        curso__periodo=instance.periodo,
    )
    cursos_actuales.update(estado_id=6)

    return


def aprobar_reintegracion(instance, estado_anterior):

    instance.estudiante.estado_estudiante_id = 4
    instance.estudiante.save()

    return


def aprobar_renuncia(instance, estado_anterior):

    instance.estudiante.estado_estudiante_id = 11  # retiro voluntario
    instance.estudiante.periodo_egreso = instance.periodo
    instance.estudiante.save()

    # no eliminar cursos cuando un estudiante está realizando el proceso de transferencia interna
    if Solicitud.objects.filter(
        estudiante=instance.estudiante,
        tipo=2,  # transferencia interna
        estado=5,  # renuncia pendiente
    ).exists():
        return

    cursos_actuales = EstudianteCurso.objects.filter(
        estudiante=instance.estudiante,
        curso__periodo=instance.periodo,
    )
    cursos_actuales.update(estado_id=7)

    return


def aprobar_transferencia_interna(instance, estado_anterior):

    if estado_anterior == 0:
        instance.estado = 5
        instance.save()

    elif estado_anterior == 5:
        instance.estudiante.estado_estudiante_id = 19
        instance.estudiante.periodo_egreso = instance.periodo
        instance.estudiante.save()

        estudiante_nuevo = Estudiante.objects.create(
            persona=instance.estudiante.persona,
            plan=Plan.objects.filter(carrera=instance.solicitudcambiocarrera.carrera)
            .order_by('-version').first(),
            periodo_ingreso=instance.periodo.get_sgte_primer_semestre(),
            estado_estudiante_id=4,
            estudiante_antiguo=instance.estudiante
        )

        # actualizar unidad organizativa usuario
        credentials = autenticar_server()
        api_google = build('admin', 'directory_v1', credentials=credentials)
        http = AuthorizedHttp(credentials=credentials, http=httplib2.Http())

        mail = estudiante_nuevo.persona.mail_institucional
        path_unidad = obtener_unidad_organizativa(api_google, http, estudiante_nuevo)
        actualizar_unidad_organizativa(api_google, http, mail, path_unidad)

    return


APROBAR_SOLICITUD_TIPO = {
    1: aprobar_postergacion,
    2: aprobar_transferencia_interna,
    3: aprobar_reintegracion,
    4: aprobar_renuncia,
}
