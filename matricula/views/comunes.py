from django.utils import timezone
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateAPIView

from rest_access_policy import AccessPolicy

from persona.permisos import AdministradoresLeerEscribir, TodosSoloLeer

from persona.models import Estudiante
from pagare.models import ModalidadCuotaPagare, Pagare

from matricula.models import (
    ProcesoMatricula, PeriodoProcesoMatricula, MatriculaEstudiante, ArancelEstudiante,
)
from matricula.serializers import (
    DetallesPeriodoProcesoMatriculaSerializer, PeriodoProcesoMatriculaSerializer,
    DatosContactoSerializer, MatriculaEstudianteSerializer, ArancelEstudianteSerializer,
    HistorialMatriculaEstudianteSerializer,
)
from matricula.utils import generar_contrato


class PeriodoProcesoMatriculaView(ListAPIView):
    queryset = PeriodoProcesoMatricula.objects.all()
    serializer_class = PeriodoProcesoMatriculaSerializer
    permission_classes = [AllowAny, ]

    def get_queryset(self):
        queryset = self.queryset.filter(
            proceso_matricula__activo=True,
            fecha_fin__gte=timezone.now(),
        )

        publico = self.request.query_params.get('publico', None)
        if publico is not None:
            queryset = queryset.filter(publico=publico)

        return queryset


@api_view(['GET'])
@permission_classes([TodosSoloLeer])
def get_detalle_periodo_actual(request):
    estudiante_id = request.query_params.get('estudiante', None)
    if estudiante_id is None:
        return Response(
            {'mensaje': 'Debe ingresar un estudiante.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que existe el estudiante enviado
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except Estudiante.DoesNotExist:
        return Response(
            {'mensaje': 'El estudiante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    # obtener periodos actuales
    periodos = PeriodoProcesoMatricula.periodos_abiertos(
        publico=estudiante.tipo_estudiante(), plan=estudiante.plan)

    if not periodos.exists():
        return Response(None)

    return Response(DetallesPeriodoProcesoMatriculaSerializer(periodos.first()).data)


# solo permitir acceder a la información propia
class PoliticaDatosContacto(AccessPolicy):
    statements = [
        {
            'action': ['retrieve', 'partial_update'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': 'es_info_propia',
        },
    ]

    def es_info_propia(self, request, view, action) -> bool:
        try:
            return request.user.persona == view.get_object()

        # caso borde en que el usuario actual no tiene una persona asociada (admins)
        except request.user._meta.model.persona.RelatedObjectDoesNotExist:
            return False


class DatosContactoViewset(RetrieveUpdateAPIView, viewsets.GenericViewSet):
    serializer_class = DatosContactoSerializer
    permission_classes = [PoliticaDatosContacto | AdministradoresLeerEscribir]

    def get_object(self):
        # esta vista recibe un id de estudiante y retorna a la persona asociada
        estudiante = get_object_or_404(Estudiante, id=self.kwargs['pk'])
        return estudiante.persona

    def partial_update(self, request, *args, **kwargs):
        # registrar etapa actual del estudiante
        estudiante = Estudiante.objects.get(id=self.kwargs['pk'])
        estudiante.registrar_etapa_matricula(etapa=2)

        return super().partial_update(request, *args, **kwargs)


# solo permitir acceder a la información propia
class PoliticaDatosEstudiante(AccessPolicy):
    statements = [
        {
            'action': ['<safe_methods>'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': 'es_info_propia',
        },
    ]

    def es_info_propia(self, request, view, action) -> bool:
        try:
            estudiante = Estudiante.objects.get(id=view.kwargs['estudiante_id'])
        except Estudiante.DoesNotExist:
            return False

        try:
            return request.user.persona == estudiante.persona

        # caso borde en que el usuario actual no tiene una persona asociada (admins)
        except request.user._meta.model.persona.RelatedObjectDoesNotExist:
            return False


class MatriculaEstudianteView(RetrieveAPIView):
    serializer_class = MatriculaEstudianteSerializer
    permission_classes = [PoliticaDatosEstudiante | AdministradoresLeerEscribir, ]

    def get_object(self):
        # esta vista recibe un id de estudiante y retorna su matrícula del proceso activo
        estudiante = Estudiante.objects.get(id=self.kwargs['estudiante_id'])

        return MatriculaEstudiante.objects.get(
            proceso_matricula__activo=True,
            estudiante=estudiante,
        )


class ArancelEstudianteView(RetrieveAPIView):
    serializer_class = ArancelEstudianteSerializer
    permission_classes = [PoliticaDatosEstudiante | AdministradoresLeerEscribir, ]

    def get_object(self):
        # esta vista recibe un id de estudiante y retorna su arancel del proceso activo
        estudiante = Estudiante.objects.get(id=self.kwargs['estudiante_id'])

        return ArancelEstudiante.objects.get(
            proceso_matricula__activo=True,
            estudiante=estudiante,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aceptar_pagare(request):
    # chequear que se envían los parámetros necesarios
    if 'estudiante' not in request.data or 'modalidad' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar un estudiante y modalidad.'},
            status=status.HTTP_400_BAD_REQUEST)

    estudiante_id = request.data['estudiante']
    modalidad_id = request.data['modalidad']

    # chequear que existe el estudiante enviado
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except Estudiante.DoesNotExist:
        return Response(
            {'mensaje': 'El estudiante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que existe la modalidad enviada
    try:
        modalidad_cuota = ModalidadCuotaPagare.objects.get(id=modalidad_id)
    except ModalidadCuotaPagare.DoesNotExist:
        return Response(
            {'mensaje': 'la modalidad enviada no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que el estudiante corresponde al usuario actual
    if request.user.persona != estudiante.persona:
        return Response(
            {'mensaje': 'Solo el estudiante puede elegir pagar con pagaré.'},
            status=status.HTTP_400_BAD_REQUEST)

    if not estudiante.habilitado_matricula():
        return Response(
            {'mensaje': 'Lo sentimos, ya no te encuentras habilitado para matricularte.'},
            status=status.HTTP_400_BAD_REQUEST)

    # obtener arancel estudiante
    proceso_matricula = ProcesoMatricula.objects.get(activo=True)
    arancel_estudiante = ArancelEstudiante.objects.get(
        estudiante=estudiante, proceso_matricula=proceso_matricula)

    # chequear que no exista una orden de compra pagada
    if arancel_estudiante.orden_compra and arancel_estudiante.orden_compra.estado_pago == 1:
        return Response(
            {'mensaje': 'Ya existe una orden de compra aprobada para tu arancel.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # chequear que no exista una orden de compra pagada
    if arancel_estudiante.pagare and arancel_estudiante.pagare.estado == 1:
        return Response(
            {'mensaje': 'Ya existe un pagaré recibido para tu arancel.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    periodos_abiertos = PeriodoProcesoMatricula.periodos_abiertos(
        publico=estudiante.tipo_estudiante(), plan=estudiante.plan)
    if not periodos_abiertos.exists():
        return Response(
            {'mensaje':
                'No puedes modificar tu forma de pago si no hay un periodo de matrícula abierto.'},
            status=status.HTTP_400_BAD_REQUEST)

    # cancelar orden de compra anterior
    if arancel_estudiante.orden_compra:
        arancel_estudiante.orden_compra.estado_pago = 4
        arancel_estudiante.orden_compra.save()

    # anular pagaré antiguo
    if arancel_estudiante.pagare:
        arancel_estudiante.pagare.estado = 8  # cancelado por cambio de forma de pago
        arancel_estudiante.pagare.save()

    pagare = Pagare(
        arancel_estudiante=arancel_estudiante,
        rut_estudiante=estudiante.persona.numero_documento,
        modalidad_cuota=modalidad_cuota,
        monto_arancel=arancel_estudiante.monto,
    )
    pagare.save()

    arancel_estudiante.pagare = pagare
    arancel_estudiante.orden_compra = None
    arancel_estudiante.pago_cuotas = True
    arancel_estudiante.periodo_matricula = periodos_abiertos.first()
    arancel_estudiante.save()

    # registrar etapa actual del estudiante
    estudiante.registrar_etapa_matricula(etapa=4)

    return Response({
        'OK': True,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumen(request, estudiante_id):
    # chequear que existe el postulante enviado
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except Estudiante.DoesNotExist:
        return Response(
            {'mensaje': 'El estudiante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que el estudiante corresponde al usuario actual
    if request.user.persona != estudiante.persona:
        return Response(
            {'mensaje': 'Solo el estudiante puede acceder a su resumen.'},
            status=status.HTTP_403_FORBIDDEN)

    proceso = ProcesoMatricula.objects.get(activo=True)
    matricula = MatriculaEstudiante.objects.get(estudiante=estudiante, proceso_matricula=proceso)
    arancel = ArancelEstudiante.objects.get(estudiante=estudiante, proceso_matricula=proceso)

    return Response({
        'estudiante': estudiante.id,
        'matricula': MatriculaEstudianteSerializer(matricula).data,
        'arancel': ArancelEstudianteSerializer(arancel).data,
        'hay_periodo_abierto': PeriodoProcesoMatricula.hay_periodo_abierto(
            publico=estudiante.tipo_estudiante(), plan=estudiante.plan,
        ),
        'habilitado': estudiante.habilitado_matricula()
    })


class HistorialMatriculaEstudianteView(ListAPIView):
    queryset = MatriculaEstudiante.objects.all()
    serializer_class = HistorialMatriculaEstudianteSerializer
    permission_classes = [AdministradoresLeerEscribir, ]

    def get_queryset(self):
        return self.queryset.filter(estudiante__persona=self.kwargs['persona_id'])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aceptar_contrato(request):
    persona = request.user.persona

    if not persona.acepta_contrato:
        try:
            generar_contrato(persona)
            persona.acepta_contrato = True
            persona.save()
            return Response(
                {'mensaje': 'Contrato aceptado con éxito.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'mensaje': 'Hubo un problema al generar el contrato. Favor intente nuevamente',
                 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif persona.acepta_contrato:
        return Response(
            {'mensaje': 'El contrato ya fue aceptado con anterioridad'},
            status=status.HTTP_400_BAD_REQUEST)
