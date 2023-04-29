from rest_framework import status, viewsets, mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view

from rest_access_policy import AccessPolicy

from persona.permisos import AdministradoresLeerEscribir, TodosSoloLeer, GRUPOS

from curso.serializers import serializar_opciones

from curso.models import EstudianteCurso
from persona.models import Persona
from certificados.models import Certificado, SolicitudCertificado
from certificados.serializers import (
    CertificadoSerializer, PostSolicitudCertificadoSerializer,
    ResolucionSolicitudCertificadoSerializer, SolicitudCertificadoSerializer,
)
from certificados.verificador import generar_certificado
from certificados.generador import previsualizar_certificado
from certificados.schema import *


@extend_schema(**validar_certificado_schema)
@api_view(['POST'])
@permission_classes([AllowAny])
def validar_certificado(request):
    folio = request.data.get('folio', None)
    llave = request.data.get('llave', None)

    if folio is None:
        return Response(
            {'mensaje': 'Debe ingresar un número de folio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if llave is None:
        return Response(
            {'mensaje': 'Debe ingresar un código de validación.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        certificado = Certificado.objects.get(pk=folio, llave=llave)
    except Certificado.DoesNotExist:
        return Response(
            {'mensaje': 'No se encontró el certificado solicitado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(CertificadoSerializer(certificado).data)


@extend_schema(**obtener_certificado_schema)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def obtener_certificado(request):
    es_secretario_academico = request.user.groups.filter(name=GRUPOS.SECRETARIO_ACADEMICO).exists()

    if es_secretario_academico and 'persona' in request.data:
        user = Persona.objects.get(id=request.data['persona']).user
    else:
        user = request.user

    estudiante = user.get_persona().estudiante_activo()

    tipo = request.data['tipo']
    certificado = generar_certificado(tipo, estudiante, request)
    serializador = CertificadoSerializer(certificado)
    return Response(serializador.data, status=status.HTTP_200_OK)


@extend_schema(**enviar_solicitud_schema)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_solicitud(request):  # Solicitud de Certificado Personalizado
    estudiante = request.user.get_persona().estudiante_activo()
    if not (estudiante.estado_estudiante_id == 4 and EstudianteCurso.objects.filter(
            estudiante=estudiante, curso__periodo__activo=True).exists()):
        raise ValidationError({
            'detail': 'Estudiante no cuenta con requisitos para obtener un certificado'
        })

    serializador = PostSolicitudCertificadoSerializer(data=request.data,
                                                      context={'request': request})
    serializador.is_valid(raise_exception=True)
    serializador.save()
    return Response(
        {
            'mensaje': 'Exito',
            'certificado': serializador.data
        },
        status=status.HTTP_200_OK)


class PermisoSolicitud(AccessPolicy):
    statements = [
        {
            'action': ['retrieve'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': ['es_solicitud_propia'],
        },
        {
            'action': ['list'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': ['son_solicitudes_propias'],
        },
        {
            'action': ['list', 'retrieve'],
            'principal': [f'group:{GRUPOS.SECRETARIO_ACADEMICO}'],
            'effect': 'allow'
        },
    ]

    def es_solicitud_propia(self, request, view, action) -> bool:
        if action in ['retrieve']:
            return view.get_object().estudiante.persona == request.user.get_persona()

        return True

    def son_solicitudes_propias(self, request, view, action) -> bool:
        persona = int(request.query_params.get('persona', -1))
        return persona == request.user.get_persona().id


@extend_schema_view(**SolicitudCertificadoViewset_schema)
class SolicitudCertificadoViewset(
        viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    queryset = SolicitudCertificado.objects.all().order_by('-fecha_solicitud')
    serializer_class = SolicitudCertificadoSerializer
    permission_classes = [PermisoSolicitud]

    def get_queryset(self):
        queryset = super().get_queryset()
        persona = self.request.query_params.get('persona', None)
        if persona is not None:
            queryset = queryset.filter(estudiante__persona=persona)
        return queryset


class PermisosEstudiante(AccessPolicy):
    statements = [
        {
            'action': ['retrieve'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': ['es_envio_propio'],
        },
        {
            'action': ['list'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': ['enlista_envios_propios'],
        },

    ]

    def es_envio_propio(self, request, view, action) -> bool:
        if action in ['retrieve']:
            return view.get_object().estudiante.persona == request.user.get_persona()
        return True
    def enlista_envios_propios(self, request, view, action) -> bool:
        persona = int(request.query_params.get('persona', -1))
        return persona == request.user.get_persona().id


class PermisosSecretarioAcademico(AccessPolicy):
    statements = [
        {
            'action': [
                'retrieve', 'list', 'anular_certificado', 'ResolucionSolicitudView',
                'previsualizar_certificado_personalizado',
            ],
            'principal': [f'group:{GRUPOS.SECRETARIO_ACADEMICO}'],
            'effect': 'allow'
        },

    ]


@extend_schema_view(**CertificadoViewSet_schema)
class CertificadoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Certificado.objects.all().order_by('-fecha_emision')
    serializer_class = CertificadoSerializer
    permission_classes = [
        PermisosSecretarioAcademico | PermisosEstudiante
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        persona = self.request.query_params.get('persona', None)
        if persona is not None:
            queryset = queryset.filter(estudiante__persona=persona)
        return queryset


@extend_schema(**TiposCertificadosView_schema)
class TiposCertificadosView(APIView):
    permission_classes = [TodosSoloLeer, ]

    def get(self, request, format=None):
        return Response(serializar_opciones(Certificado.tipos_certificado))


@extend_schema(**anular_certificado_schema)
@api_view(['POST'])
@permission_classes([PermisosSecretarioAcademico])
def anular_certificado(request):
    id_certifcado = request.data['certificado']
    try:
        certificado = Certificado.objects.get(pk=id_certifcado)
    except Certificado.DoesNotExist:
        return Response(
            {'mensaje': 'No se encontró el certificado solicitado.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    certificado.valido = False
    certificado.save()
    serializador = CertificadoSerializer(certificado)
    return Response(
        {
            'mensaje': 'Exito',
            'certificado': serializador.data
        },
        status=status.HTTP_200_OK)


@extend_schema(**previsualizar_certificado_personalizado_schema)
@api_view(['POST'])
@permission_classes([PermisosSecretarioAcademico | AdministradoresLeerEscribir])
def previsualizar_certificado_personalizado(request):
    contexto = {
        'titulo': request.data['titulo'],
        'contenido': request.data['contenido'],
    }
    return previsualizar_certificado('personalizado.html', contexto)


@extend_schema(**ResolucionSolicitudView_schema)
class ResolucionSolicitudView(UpdateAPIView):
    queryset = SolicitudCertificado.objects.all()
    serializer_class = ResolucionSolicitudCertificadoSerializer
    permission_classes = [PermisosSecretarioAcademico | AdministradoresLeerEscribir]
