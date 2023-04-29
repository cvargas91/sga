import os

from django.contrib.auth.models import Group

from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import AccessToken

from rest_access_policy import AccessPolicy

from google_auth_oauthlib.flow import Flow
from google.auth import jwt

from academica.models import Plan
from academica.serializers import PlanCortoSerializer
from curso.models import Periodo
from curso.serializers import PeriodoSerializer

from .models import Persona, Estudiante, EstadoEstudiante, HistorialEstadoEstudiante
from .serializers import (
    UsuarioSerializer, PersonaSerializer, MonitoreoEstudiantesSerializer, PerfilPrivadoSerializer,
    PerfilPublicoSerializer, FotoPerfilSerializer, GroupSerializer, PersonaCortaSerializer,
    EstadoEstudianteSerializer, HistorialEstadoEstudianteSerializer, EstudianteSerializer,
    ResumenAcademicoSerializer,
)
from .permisos import AdministradoresLeerEscribir, TodosSoloLeer, GRUPOS


archivo_configuracion = ''
for file in os.listdir('config/'):
    if file.endswith('.apps.googleusercontent.com.json'):
        archivo_configuracion = os.path.join('config', file)


flow = Flow.from_client_secrets_file(
    archivo_configuracion,
    scopes=[
        'openid',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
    ],
    redirect_uri='postmessage')

## Login antiguo (EOL 03/2023)
## TODO: Actualizar login en SGA-Frontend 
@api_view(['POST'])
@permission_classes([AllowAny])
def login_google(request):
    if 'code' not in request.data:
        return Response(
            {'mensaje': 'Debe enviar un código de confirmación de google.'},
            status=status.HTTP_400_BAD_REQUEST)

    # obtener tokens con el código
    try:
        flow.fetch_token(code=request.data['code'])
    except Exception:
        return Response(
            {'mensaje': 'El código entregado no es válido.'},
            status=status.HTTP_400_BAD_REQUEST)

    # solicitar información de google
    try:
        session = flow.authorized_session()
        user_info = session.get('https://www.googleapis.com/userinfo/v2/me').json()
    except Exception:
        return Response(
            {'mensaje': 'Ha habido un error al comunicarse con el servicio de google.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # encontrar usuario asociado
    try:
        email = user_info['email']
        persona = Persona.objects.get(mail_institucional=email)
    except Persona.DoesNotExist:
        return Response(
            {'mensaje': 'Lo sentimos, el correo utilizado no está asociado a un usuario.'},
            status=status.HTTP_400_BAD_REQUEST)

    # retornar token
    access_token = AccessToken.for_user(persona.user)

    return Response({
        'usuario': UsuarioSerializer(persona, context={'request': request}).data,
        'accessToken': str(access_token),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_jwt(request):
    if 'jwt' not in request.data:
        return Response(
            {'mensaje': 'Debe enviar un JSON Web Token para validación.'},
            status=status.HTTP_400_BAD_REQUEST)

    payload = jwt.decode(request.data.get('jwt'), verify=False)

    # encontrar usuario asociado
    try:
        email = payload['email']
        persona = Persona.objects.get(mail_institucional=email)
    except Persona.DoesNotExist:
        return Response(
            {'mensaje': 'Lo sentimos, el correo utilizado no está asociado a un usuario.'},
            status=status.HTTP_400_BAD_REQUEST)

    # retornar token
    access_token = AccessToken.for_user(persona.user)

    return Response({
        'usuario': UsuarioSerializer(persona, context={'request': request}).data,
        'accessToken': str(access_token),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def validar_token(request):
    if 'token' not in request.data:
        return Response(
            {'mensaje': 'Debe enviar un token para validación.'},
            status=status.HTTP_400_BAD_REQUEST)

    try:
        access_token = AccessToken(token=request.data['token'])
    except Exception:
        return Response(
            {'mensaje': 'El token no es válido o ya expiró.'},
            status=status.HTTP_400_BAD_REQUEST)

    # obtener información de usuario
    persona = Persona.objects.get(user=access_token.payload['user_id'])
    return Response({
        'usuario': UsuarioSerializer(persona, context={'request': request}).data,
        'accessToken': str(access_token),
    })


class PoliticaPerfil(AccessPolicy):
    statements = [
        {  # permitir editar el perfil propio
            'action': ['<method:patch>'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': ['es_perfil_propio'],
        },
    ]

    def es_perfil_propio(self, request, view, action) -> bool:
        return view.es_perfil_propio()


class PerfilView(RetrieveUpdateAPIView):
    queryset = Persona.objects.all()
    permission_classes = [PoliticaPerfil | TodosSoloLeer | AdministradoresLeerEscribir, ]
    grupos_privilegiados = [GRUPOS.ADMINISTRADORES, GRUPOS.FINANZAS]

    def get_serializer_class(self):
        es_usuario_privilegiado = self.request.user.groups.filter(
            name__in=self.grupos_privilegiados
        ).exists()

        if es_usuario_privilegiado or self.es_perfil_propio():
            return PerfilPrivadoSerializer

        return PerfilPublicoSerializer

    def es_perfil_propio(self):
        return self.request.user.get_persona() == self.get_object()


class FotoPerfilView(PerfilView):
    def get_serializer_class(self):
        return FotoPerfilSerializer


class MonitoreoEstudiantesView(viewsets.ReadOnlyModelViewSet):
    queryset = Persona.objects.prefetch_related(
        'estudiantes__plan',
        'estudiantes__estado_estudiante',
        'estudiantes__periodo_ingreso',
        'estudiantes__periodo_egreso',
    )
    serializer_class = MonitoreoEstudiantesSerializer
    permission_classes = [AdministradoresLeerEscribir, ]

    def get_queryset(self):
        ids_estudiantes = Estudiante.objects.values_list('persona')
        return self.queryset.filter(id__in=ids_estudiantes)


class OpcionesMonitoreoView(APIView):
    permission_classes = [AdministradoresLeerEscribir, ]

    def get(self, request, format=None):
        return Response({
            'planes': PlanCortoSerializer(Plan.objects.all(), many=True).data,
            'estados': EstadoEstudianteSerializer(EstadoEstudiante.objects.all(), many=True).data,
            'periodos_ingreso': PeriodoSerializer(Periodo.objects.all(), many=True).data,
        })


class PersonaViewSet(viewsets.ModelViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [AdministradoresLeerEscribir, ]


class GroupView(ListAPIView):
    queryset = Group.objects.all()
    permission_classes = [AdministradoresLeerEscribir, ]
    serializer_class = GroupSerializer


class PersonaRolView(ListAPIView):
    queryset = Persona.objects.all()
    serializer_class = PersonaCortaSerializer
    permission_classes = [AdministradoresLeerEscribir, ]

    def get_queryset(self):
        queryset = super().get_queryset()

        rol = self.request.query_params.get('rol', None)
        if rol is not None:
            queryset = queryset.filter(user__groups__name=rol)

        return queryset


class HistorialEstadoEstudianteView(ListAPIView):
    queryset = HistorialEstadoEstudiante.objects.all()
    serializer_class = HistorialEstadoEstudianteSerializer
    permission_classes = [AdministradoresLeerEscribir, ]

    def get_queryset(self):
        return self.queryset.filter(
            estudiante__persona=self.kwargs['pk']
        ).order_by('periodo', 'creado')


class EstudianteViewSet(viewsets.ModelViewSet):
    queryset = Estudiante.objects.all()
    serializer_class = EstudianteSerializer
    permission_classes = [AdministradoresLeerEscribir, ]


class ResumenAcademicoView(RetrieveAPIView):
    queryset = Estudiante.objects.prefetch_related(
        'plan',
        'estado_estudiante',
        'periodo_ingreso',
        'periodo_egreso',
        'cursos__estado',
    )
    serializer_class = ResumenAcademicoSerializer
    permission_classes = [AdministradoresLeerEscribir, ]
