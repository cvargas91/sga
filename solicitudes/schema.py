from drf_spectacular.utils import (inline_serializer, extend_schema,
                                   OpenApiParameter, PolymorphicProxySerializer)
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers

from solicitudes.serializers import (EnvioSolicitudCambioCarreraSerializer,
                                     EnvioSolicitudPostergacionSerializer)

# diccionarios estructurados como parámetros para @extend_schema drf-spectacular

enviar_solicitud_schema = dict(
    summary="Enviar Solicitud",
    description='Acepta una request con los campos de una Solicitud Base y crea una nueva '
                'Solicitud. Adicionalmente, requiere incluir de forma anidada los valores '
                'requeridos según el tipo de Solicitud (Ej: id de Carrera en Solicitud '
                'de Transferencia Interna',
    request=inline_serializer(
        name="EnviarSolicitudSerializer",
        fields={
            "solicitud": inline_serializer(
                name="EnviarSolicitudBaseSerializer",
                fields={
                    "tipo": serializers.IntegerField(),
                    "periodo": serializers.IntegerField(),
                    "causas_estudiante": serializers.ListField(
                        child=serializers.IntegerField()),
                    "justificacion_estudiante": serializers.CharField()
                }
            ),
            "carrera": serializers.IntegerField(),
            "duracion_semestres": serializers.IntegerField()}),
    responses={
        200: PolymorphicProxySerializer(
            component_name='EnvioSerializer',
            serializers=[
                EnvioSolicitudCambioCarreraSerializer, EnvioSolicitudPostergacionSerializer,
                EnvioSolicitudPostergacionSerializer, EnvioSolicitudCambioCarreraSerializer
            ],
            resource_type_field_name='solicitud')
    }
)

EstadoSolicitudView_schema = dict(
    summary="Obtener Estados de Solicitudes",
    request=None,
    responses={
        200: inline_serializer(
            name="EstadoSolicitudSerializer",
            fields={"id": serializers.IntegerField(),
                    "valor": serializers.CharField()}),
    },
    description='Retorna una lista con todos los Estados de Solicitudes.')


ResolucionSolicitudView_schema = dict(
    summary="Resolver Solicitud",
    description='Recibe como parámetro el Id de una Solicitud pendiente. Si el usuario '
                'pertenece al grupo Secretaría Académica, actualiza la Solicitud '
                'con los valores ingresados en la revisión.'
)

SolicitudView_schema = dict(
    summary="Obtener Solicitudes",
    description='Retorna una lista con todas las Solicitudes existentes. Si el usuario '
                'pertenece al grupo Estudiante, solo recibe las Solicitudes '
                'que tengan su propio ID de Estudiante. Opcionalmente, acepta '
                'parámetros para filtrar Solicitudes según Estado y Persona',
    parameters=[
        OpenApiParameter(
            name='id_estado',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY),
        OpenApiParameter(
            name='id_persona',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY)
            ]

)

SolicitudDetalleView_schema = dict(
    summary="Obtener Solicitud",
    description='Recibe como parámetro el Id de una Solicitud y lo retorna. Incluye '
                'también un objeto anidado "detalle" con el contenido de la Solicitud '
                'especifica asociada a la Solicitud Base. Si el usuario pertenece al grupo '
                'Estudiante, el campo "comentario_revisor" se oculta.'
)

TipoSolicitudView_schema = dict(
    summary="Obtener Tipos de Solicitudes",
    description='Retorna una lista con todos los Tipos de Solicitudes. Opcionalmente, acepta'
                'un parámetro id_persona para retonar solo los Tipos de Solicitudes disponibles'
                'para la persona según su estado',
    request=None,
    responses={
        200: inline_serializer(
            name="TiposCertificadoSerializer",
            fields={"id": serializers.IntegerField(),
                    "nombre": serializers.CharField(),
                    "instrucciones": serializers.CharField()}),
    },
    parameters=[
        OpenApiParameter(
            name='id_persona',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY)]
)

DecretoResolucionSolicitudView_schema = dict(
    summary="Actualizar Solicitud Aprobada",
    description='Recibe como parámetro el Id de una Solicitud. Permite a los  '
                'usuarios del grupo Secretaría Académica modificar la resolución '
                'y otros campos a una Solicitud que fue aprobada previamente '
)

# diccionarios estructurados como parámetros para @extend_schema_view drf-spectacular

CausaSolicitudViewSet_schema = dict(
    list=extend_schema(summary="Obtener Causas de Solicitudes",
                       description='Retorna todas las Causas de Solicitudes existentes'),

    retrieve=extend_schema(summary="Obtener Causa de Solicitud",
                           description='Recibe como parámetro el ID de una CausaSolicitud '
                           'y la retorna',
                           parameters=[OpenApiParameter(
                               name='id',
                               type=OpenApiTypes.INT,
                               location=OpenApiParameter.PATH)]),

    create=extend_schema(summary="Crear Causa de Solicitud",
                         description='Crea una nueva Causa de Solicitud'),

    update=extend_schema(summary="Actualizar Causa de Solicitud",
                         description='Actualiza una Causa de Solicitud'),

    partial_update=extend_schema(summary="Actualizar Causa de Solicitud",
                                 description='Actualiza una Causa de Solicitud'),

    destroy=extend_schema(summary="Eliminar Causa de Solicitud",
                          description='Elimina una Causa de Solicitud')

)

PeriodoTipoSolicitudViewSet_schema = dict(
    list=extend_schema(summary="Obtener Periodos de Tipos de Solicitudes",
                       description='Retorna todos los PeriodoTipoSolicitud existentes'),

    retrieve=extend_schema(summary="Obtener Periodo de Tipo de Solicitud",
                           description='Recibe como parámetro el ID de un PeriodoTipoSolicitud '
                           'y lo retorna',
                           parameters=[OpenApiParameter(
                               name='id',
                               type=OpenApiTypes.INT,
                               location=OpenApiParameter.PATH)]),

    create=extend_schema(summary="Crear Periodo de Tipo de Solicitud",
                         description='Crea un nuevo PeriodoTipoSolicitud'),

    update=extend_schema(summary="Actualizar Periodo de Tipo de Solicitud",
                         description='Actualiza un PeriodoTipoSolicitud'),

    partial_update=extend_schema(summary="Actualizar Periodo de Tipo de Solicitud",
                                 description='Actualiza un PeriodoTipoSolicitud'),

    destroy=extend_schema(summary="Eliminar Periodo de Tipo de Solicitud",
                          description='Elimina un PeriodoTipoSolicitud')
)
