from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_access_policy import AccessPolicy

from persona.permisos import (
    GRUPOS, AdministradoresLeerEscribir, LeerInfoPropia, TodosSoloLeer
)

from curso.serializers import CursoSerializer

from .models import (
    ProcesoInscripcion, EnvioInscripcion, SolicitudCurso,
)
from .serializers import (
    ProcesoInscripcionSerializer, EnvioInscripcionSerializer,
    SolicitudCursoSerializer, cursos_inscribibles,
)


class PermisosSecretario(AccessPolicy):
    statements = [
        {
            'action': ['create', 'update', 'partial_update'],
            'principal': f'group:{GRUPOS.SECRETARIO_ACADEMICO}',
            'effect': 'allow',
        }
    ]


class SolicitudCursoViewset(viewsets.ReadOnlyModelViewSet):
    queryset = SolicitudCurso.objects.all()
    serializer_class = SolicitudCursoSerializer
    permission_classes = [TodosSoloLeer]


class ProcesoInscripcionViewset(viewsets.ModelViewSet):
    queryset = ProcesoInscripcion.objects.all()
    serializer_class = ProcesoInscripcionSerializer
    permission_classes = [TodosSoloLeer | PermisosSecretario | AdministradoresLeerEscribir]

    def get_queryset(self):
        queryset = self.queryset

        if self.request.user.groups.filter(name=GRUPOS.ESTUDIANTES).exists():
            estudiante = self.request.user.get_persona().estudiante_activo()
            # si el usuario es estudiante, excluir procesos excepcionales que no le corresponden
            for proceso in queryset:
                if (proceso.estudiante.exists()):
                    if (estudiante not in proceso.estudiante.all()):
                        queryset = queryset.exclude(pk=proceso.pk)

        return queryset


# restringir modificaciones fuera de fechas del proceso
class PermisosEnvios(AccessPolicy):
    statements = [
        {
            'action': ['create', 'update', 'partial_update'],
            'principal': '*',
            'effect': 'allow',
            'condition': ['es_envio_propio', 'esta_activo'],
        },
        {
            'action': ['list', 'retrieve'],
            'principal': '*',
            'effect': 'allow',
            'condition': 'es_envio_propio',
        },
    ]

    def esta_activo(self, request, view, action) -> bool:
        if action == 'list':
            return True

        if action == 'create':
            proceso = ProcesoInscripcion.objects.get(pk=request.data['proceso'])
            return proceso.get_estado() == 1

        envio = view.get_object()
        return envio.proceso.get_estado() == 1

    def es_envio_propio(self, request, view, action) -> bool:
        persona = request.user.get_persona().id

        if action == 'list':
            if 'persona' in request.query_params:
                return int(request.query_params['persona']) == persona
            return False

        if 'persona' in request.data:
            if int(request.data['persona']) != persona:
                return False
            if action == 'create':
                return True

        envio = view.get_object()
        return envio.persona_id == persona


class EnvioInscripcionViewset(viewsets.ModelViewSet):
    queryset = EnvioInscripcion.objects.all()
    serializer_class = EnvioInscripcionSerializer
    permission_classes = [PermisosEnvios]

    def get_queryset(self):
        queryset = self.queryset

        persona = self.request.query_params.get('persona', None)
        if persona is not None:
            queryset = queryset.filter(persona=persona)

        proceso = self.request.query_params.get('proceso', None)
        if proceso is not None:
            queryset = queryset.filter(proceso=proceso)

        return queryset


class CursosInscribiblesView(APIView):
    permission_classes = [LeerInfoPropia | AdministradoresLeerEscribir]

    def get(self, request, format=None):
        if 'persona' not in self.request.query_params:
            return Response(
                {'detail': 'Debe enviar una persona.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if 'periodo' not in self.request.query_params:
            return Response(
                {'detail': 'Debe enviar un periodo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CursoSerializer(
            cursos_inscribibles(
                self.request.query_params.get('persona'),
                self.request.query_params.get('periodo'),
            ),
            many=True
        )
        return Response(serializer.data)
