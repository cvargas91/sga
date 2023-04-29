from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView

from persona.permisos import AdministradoresLeerEscribir, TodosSoloLeer, LeerInfoPropia

from persona.models import Estudiante

from curso.serializers import serializar_opciones

from .models import (
    Departamento, Carrera, Plan, Ramo, ConjuntoRamos, Malla,
)
from .serializers import (
    DepartamentoSerializer, CarreraSerializer, PlanSerializer, MallaPlanSerializer, RamoSerializer,
    ConjuntoRamosSerializer,
)


class DepartamentoViewSet(viewsets.ModelViewSet):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir, ]


class CarreraViewSet(viewsets.ModelViewSet):
    queryset = Carrera.objects.all()
    serializer_class = CarreraSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir, ]


class TiposCarrerasView(APIView):
    permission_classes = [TodosSoloLeer, ]

    def get(self, request, format=None):
        return Response(serializar_opciones(Carrera.tipos_carreras))


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir, ]


class MallaPlanViewSet(ListAPIView, RetrieveUpdateAPIView, viewsets.GenericViewSet):
    queryset = Plan.objects.all()
    serializer_class = MallaPlanSerializer
    permission_classes = [LeerInfoPropia | AdministradoresLeerEscribir, ]

    def get_queryset(self):
        queryset = self.queryset

        persona = self.request.query_params.get('persona', None)
        if persona is not None:
            planes = Estudiante.objects.filter(persona=persona).values('plan')
            queryset = queryset.filter(pk__in=planes)

        return queryset


class TiposFormacionView(APIView):
    permission_classes = [TodosSoloLeer, ]

    def get(self, request, format=None):
        return Response(serializar_opciones(Malla.tipos_formacion))


class RamoViewSet(viewsets.ModelViewSet):
    queryset = Ramo.objects.all()
    serializer_class = RamoSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir, ]


class ConjuntoRamosViewSet(viewsets.ModelViewSet):
    queryset = ConjuntoRamos.objects.all()
    serializer_class = ConjuntoRamosSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir, ]
