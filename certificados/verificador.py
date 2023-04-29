from datetime import timedelta

from django.utils import timezone
from rest_framework.serializers import ValidationError

from persona.permisos import GRUPOS

from certificados.generador import (
    crear_certificado_estudiante_regular, crear_certificado_matricula, crear_certificado_notas,
    crear_certificado_personalizado,
)
from certificados.models import Certificado

from curso.models import EstudianteCurso
from matricula.models import MatriculaEstudiante


def verificar_estudiante_regular(estudiante, request) -> Certificado:
    if estudiante.estado_estudiante_id == 4 and EstudianteCurso.objects.filter(
            estudiante=estudiante, curso__periodo__activo=True).exists():
        certificado = crear_certificado_estudiante_regular(estudiante)
    else:
        raise ValidationError({
            'detail': 'Estudiante no cuenta con requisitos para obtener el certificado',
        })
    return certificado


def verificar_matricula(estudiante, request) -> Certificado:
    if MatriculaEstudiante.objects.filter(
        estudiante=estudiante, proceso_matricula__activo=True, estado=1,
    ).exists():
        certificado = crear_certificado_matricula(estudiante)
    else:
        raise ValidationError({
            'detail': 'Estudiante no cuenta con matrícula válida para el periodo activo',
        })

    return certificado


def verificar_notas(estudiante, request) -> Certificado:
    if estudiante.estado_estudiante_id == 4 and EstudianteCurso.objects.filter(
            estudiante=estudiante, curso__periodo__activo=True).exists():

        certificado = crear_certificado_notas(estudiante)
    else:
        raise ValidationError({
            'detail': 'Estudiante no cuenta con requisitos para obtener el certificado',
        })

    return certificado


def verificar_personalizado(estudiante, request):
    if not request.user.groups.filter(name=GRUPOS.SECRETARIO_ACADEMICO).exists():
        raise ValidationError({
            'detail': 'Solo el secretario académico puede crear certificados personalizados',
        })

    if 'titulo' not in request.data or 'contenido' not in request.data:
        raise ValidationError({
            'detail': 'Debe incluir un titulo y contenido para el certificado personalizado',
        })

    if (estudiante.estado_estudiante_id == 4 and EstudianteCurso.objects.filter(
            estudiante=estudiante, curso__periodo__activo=True).exists()):
        return crear_certificado_personalizado(
            estudiante, request.data['titulo'], request.data['contenido'])

    else:
        raise ValidationError({
            'detail': 'Estudiante no cuenta con requisitos para obtener un certificado'
        })


VERIFICAR_CERTIFICADO_TIPO = {
    0: verificar_estudiante_regular,
    1: verificar_matricula,
    2: verificar_notas,
    3: verificar_personalizado,
}


def generar_certificado(tipo: int, estudiante, request) -> Certificado:
    tipo_verificador = VERIFICAR_CERTIFICADO_TIPO.get(tipo, None)

    if tipo_verificador is None:
        raise ValidationError({'detail': 'el tipo de certificado no está soportado'})

    # chequear que no se haya emitido este certificado en las últimas 24 horas
    ult_24hrs = timezone.now() - timedelta(days=1)
    emitido = Certificado.objects.filter(
        estudiante=estudiante,
        tipo_certificado=tipo,
        fecha_emision__gte=ult_24hrs,
    ).exists()
    if tipo != 3 and emitido:
        raise ValidationError({
            'detail': 'Solo se puede emitir un certificado por tipo cada 24 horas.'
        })

    return tipo_verificador(estudiante, request)
