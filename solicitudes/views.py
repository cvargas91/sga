from imghdr import tests
from django.utils import timezone
from rest_framework.serializers import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, extend_schema_view
from persona.models import Persona
from solicitudes.schema import *

from persona.permisos import AdministradoresLeerEscribir, TodosSoloLeer

from .models import Solicitud, TipoSolicitud, CausaSolicitud, PeriodoTipoSolicitud
from .permisos import SolicitudPermisos, ResolucionPermisos
from .serializers import (
    SolicitudDetalleSerializer, SolicitudSerializer, TipoSolicitudSerializer,
    CausaSolicitudSerializer, SERIALIZADOR_TIPO, ResolucionSolicitudSerializer,
    PeriodoTipoSolicitudSerializer, DecretoResolucionSolicitudSerializer
)
from curso.serializers import serializar_opciones


@extend_schema_view(**CausaSolicitudViewSet_schema)
class CausaSolicitudViewSet(viewsets.ModelViewSet):
    queryset = CausaSolicitud.objects.all()
    serializer_class = CausaSolicitudSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir]


@extend_schema_view(**PeriodoTipoSolicitudViewSet_schema)
class PeriodoTipoSolicitudViewSet(viewsets.ModelViewSet):
    queryset = PeriodoTipoSolicitud.objects.all()
    serializer_class = PeriodoTipoSolicitudSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir]


@extend_schema(**TipoSolicitudView_schema)
class TipoSolicitudView(ListAPIView):
    queryset = TipoSolicitud.objects.all()
    serializer_class = TipoSolicitudSerializer
    permission_classes = [TodosSoloLeer]

    def get_queryset(self):
        queryset = super().get_queryset()

        persona = self.request.query_params.get('persona', None)
        if persona is not None:
            estado_est = Persona.objects.get(pk=persona).estudiante_activo().estado_estudiante
            queryset = queryset.filter(estados_validos=estado_est)

            periodos_abiertos = PeriodoTipoSolicitud.objects.filter(
                fecha_inicio__lte=timezone.now(),
                fecha_fin__gte=timezone.now(),
            ).values_list('tipo_solicitud', flat=True)
            queryset = queryset.filter(pk__in=periodos_abiertos)

        return queryset


@extend_schema(**EstadoSolicitudView_schema)
class EstadoSolicitudView(APIView):
    permission_classes = [TodosSoloLeer, ]

    def get(self, request, format=None):
        return Response(serializar_opciones(Solicitud.estados_solicitud))


@extend_schema(**SolicitudView_schema)
class SolicitudView(ListAPIView):
    queryset = Solicitud.objects.select_related(
        'estudiante__persona', 'estudiante__plan__carrera', 'tipo')
    serializer_class = SolicitudSerializer
    permission_classes = [SolicitudPermisos | AdministradoresLeerEscribir]

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.query_params.get('estado', None)

        if estado is not None:
            if estado == '0':
                queryset = queryset.filter(estado__in=[0, 5])
            else:
                queryset = queryset.filter(estado=estado)

        persona = self.request.query_params.get('persona', None)
        if persona is not None:
            queryset = queryset.filter(estudiante__persona=persona)

        return queryset.order_by('-fecha_creacion')


@extend_schema(**SolicitudDetalleView_schema)
class SolicitudDetalleView(RetrieveAPIView):
    queryset = Solicitud.objects.all()
    serializer_class = SolicitudDetalleSerializer
    permission_classes = [SolicitudPermisos]


@extend_schema(**enviar_solicitud_schema)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_solicitud(request):
    try:
        tipo = request.data['solicitud']['tipo']
        # get user from request
        estudiante = request.user.get_persona().estudiante_activo()
    except (KeyError, TypeError):  # TODO: documentar estructura esperada de request.data
        raise ValidationError('La solicitud base no es válida')
    clase_serializador = SERIALIZADOR_TIPO.get(tipo, None)
    if request.data['solicitud']['tipo'] == 2:
        if estudiante.plan.carrera.id == request.data['carrera']:
            raise ValidationError('La carrera a cambiarse no puede ser la misma que ya esta cursando')
    if clase_serializador is None:
        raise ValidationError('el tipo de solicitud no está soportado')

    if not PeriodoTipoSolicitud.objects.filter(
            fecha_inicio__lte=timezone.now(),
            fecha_fin__gte=timezone.now(),
            tipo_solicitud=tipo).exists():
        raise ValidationError('no existe un periodo abierto para enviar la solicitud académica')

    serializador = clase_serializador(data=request.data, context={'request': request})
    serializador.is_valid(raise_exception=True)
    serializador.save()
    return Response(
        {
            'mensaje': 'Exito',
            'solicitud': serializador.data
        },
        status=status.HTTP_200_OK,
    )


@extend_schema(**ResolucionSolicitudView_schema)
class ResolucionSolicitudView(UpdateAPIView):
    queryset = Solicitud.objects.all()
    serializer_class = ResolucionSolicitudSerializer
    permission_classes = [ResolucionPermisos]


@extend_schema(**DecretoResolucionSolicitudView_schema)
class DecretoResolucionSolicitudView(UpdateAPIView):
    queryset = Solicitud.objects.all()
    serializer_class = DecretoResolucionSolicitudSerializer
    permission_classes = [ResolucionPermisos | AdministradoresLeerEscribir]

    def get_queryset(self):
        queryset = super().get_queryset().filter(estado=1)
        return queryset
