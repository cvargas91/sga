from drf_spectacular.utils import inline_serializer, extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from certificados.serializers import (CertificadoSerializer, PostSolicitudCertificadoSerializer,
                                      ResolucionSolicitudCertificadoSerializer)

# diccionarios estructurados como parámetros para @extend_schema
anular_certificado_schema = dict(
    summary="Anular Certificado",
    request=inline_serializer(
        name="IDCertificadoSerializer",
        fields={"certificado": serializers.IntegerField()}),
    responses={
        200: CertificadoSerializer,
        404: inline_serializer(
            name="MensajeSerializer",
            fields={"mensaje": serializers.CharField()}),
    },
    description='Recibe el ID de un certificado. Si el usuario pertenece al grupo Secretario '
                'Académico, modifica el certificado cambiando el booleano Valido a False',
)

TiposCertificadosView_schema = dict(
    summary="Obtener Tipos de Certificados",
    request=None,
    responses={
        200: inline_serializer(
            name="TiposCertificadoSerializer",
            fields={"id": serializers.IntegerField(),
                    "valor": serializers.CharField()}),
    },
    description='Retorna una lista con todos los Tipos de Certificado'
)

obtener_certificado_schema = dict(
    summary="Obtener certificado",
    request=inline_serializer(
        name="TipoCertificadoSerializer",
        fields={"tipo": serializers.IntegerField(),
                "estudiante": serializers.IntegerField()}),
    responses={
        200: CertificadoSerializer,
    },
    description='Recibe el ID de un tipo de certificado, y obtiene automáticamente el estudiante '
                'asociado a la request. Si Estudiante cuenta con los requisitos (verificador.py), '
                'retorna un nuevo Certificado. Opcionalmente, usuarios del grupo Secretaría '
                'Académica pueden incluir el ID de cualquier Estudiante '
)

enviar_solicitud_schema = dict(
    summary="Enviar Solicitud de Certificado Personalizado",
    request=PostSolicitudCertificadoSerializer,
    responses={
        200: PostSolicitudCertificadoSerializer,
    },
    description='Captura al Estudiante asociado a la request. Si cuenta con los requisitos '
                '(verificador.py), se crea un registro en SolicitudCertificado '
)


previsualizar_certificado_personalizado_schema = dict(
    summary="Previsualizar Certificado Personalizado",
    request=inline_serializer(
        name="PrevisualizarCertificadoSerializer",
        fields={"titulo": serializers.CharField(),
                "contenido": serializers.CharField()}),
    responses={
        200: None
    },
    description='Recibe un título y contenido para previsualizar un Certificado Personalizado '
                'en el navegador. No se crea un registro en SolicitudCertificado '
)

validar_certificado_schema = dict(
    summary="Validar Certificado",
    parameters=[
        OpenApiParameter(
            name='folio',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY),
        OpenApiParameter(
            name='llave',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY)
    ],
    request=None,
    responses={
        200: CertificadoSerializer
    },
    description='Recibe un folio y llave de un Certificado. Si son válidos,  '
                'retorna el Certificado'
)


ResolucionSolicitudView_schema = dict(
    summary="Resolver Solicitud",
    request=ResolucionSolicitudCertificadoSerializer,
    description='Recibe el ID de una SolicitudCertificado. Si el usuario pertenece al grupo  '
                'Secretario Académico, y la solicitud se encuentra en estado pendiente, '
                'se actualiza la SolicitudCertificado con los datos del revisor',
    parameters=[OpenApiParameter(
        name='id',
        type=OpenApiTypes.INT,
        location=OpenApiParameter.PATH)]
)

# diccionarios estructurados como parámetros para @extend_schema_view

CertificadoViewSet_schema = dict(
    retrieve=extend_schema(summary="Obtener Certificado",
                           description='Recibe como parámetro el ID de un certificado y lo retorna',
                           parameters=[OpenApiParameter(
                               name='id_certificado',
                               type=OpenApiTypes.INT,
                               location=OpenApiParameter.PATH)]),

    list=extend_schema(summary="Obtener Certificados",
                       description='Retorna todos los Certificados existentes. Opcionalmente, '
                       'permite filtrar los Certificados usando el parámetro id_persona',
                       parameters=[
                           OpenApiParameter(
                               name='id_persona',
                               type=OpenApiTypes.INT,
                               location=OpenApiParameter.QUERY)]))

SolicitudCertificadoViewset_schema = dict(
    list=extend_schema(summary="Obtener Solicitudes de Certificados Personalizados",
                       description='Retorna todas las Solicitudes de Certificados personalizados. '
                       'Opcionalmente, permite filtrar las Solicitudes de Certificados usando '
                       'el parámetro id_persona',
                       parameters=[
                           OpenApiParameter(
                               name='id_persona',
                               type=OpenApiTypes.INT,
                               location=OpenApiParameter.QUERY)]),

    retrieve=extend_schema(summary="Obtener Solicitud de Certificado Personalizado",
                           description='Recibe como parámetro el ID de una SolicitudCertificado '
                           'y la retorna',
                           parameters=[OpenApiParameter(
                               name='id_certificado',
                               type=OpenApiTypes.INT,
                               location=OpenApiParameter.PATH)]),

)
