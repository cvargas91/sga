from rest_framework import viewsets, mixins, status
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet
from rest_framework.generics import (RetrieveAPIView, ListAPIView, RetrieveUpdateAPIView,
                                     GenericAPIView,)
from rest_framework.mixins import ListModelMixin, UpdateModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.serializers import ValidationError
from rest_access_policy import AccessPolicy
from persona.models import Persona

from persona.permisos import (
    AdministradoresLeerEscribir, LeerInfoPropia, LeerInfoPropiaOpcional, TodosSoloLeer,
)
from .models import (
    Actividad, CategoriaActividad, Curso, Evaluacion, Horario, DocenteCurso, Modulo, Periodo,
    EstudianteCurso, Nota
)
from .serializers import (
    ActividadSerializer, EvaluacionSerializer, PeriodoSerializer, ModuloSerializer, CursoSerializer,
    CursoIntegrantesSerializer, CursoHorarioSerializer, HistorialCursosSerializer,
    serializar_opciones, CategoriaActividadSerializer, CursoResumenSerializer,
    ActividadesCursoSerializer, EvaluacionesActividadSerializer, EvaluacionesCursoSerializer,
    NotaEvaluacionSerializer, EnvioNotasEvaluacionSerializer, CursoEstudiantesSerializer,
    ConfiguracionCursoSerializer, NotasPresentacionSerializer, NotasFinalesSerializer,
    NotasExamenCursoSerializer, VistaResumenCursoSerializer, NotasVistaResumenSerializer
)
from rest_framework.permissions import AllowAny


class PeriodoViewSet(viewsets.ModelViewSet):
    queryset = Periodo.objects.all()
    serializer_class = PeriodoSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir, ]


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [LeerInfoPropiaOpcional | AdministradoresLeerEscribir, ]

    def get_queryset(self):
        queryset = self.queryset

        periodo = self.request.query_params.get('periodo', None)
        if periodo is not None:
            # permitir filtrar por periodo activo
            if periodo == 'activo':
                periodo = Periodo.get_activo()
            queryset = queryset.filter(periodo=periodo)

        depto = self.request.query_params.get('depto', None)
        if depto is not None:
            queryset = queryset.filter(ramo__departamento=depto)

        persona = self.request.query_params.get('persona', None)
        if persona is not None:
            inscritos = EstudianteCurso.objects.filter(estudiante__persona=persona).values('curso')
            queryset = queryset.filter(pk__in=inscritos)

        return queryset


class CursoResumenViewSet(CursoViewSet):
    serializer_class = CursoResumenSerializer


class CursoHorarioView(RetrieveAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoHorarioSerializer
    permission_classes = [TodosSoloLeer, ]


class PoliticaIntegrantes(AccessPolicy):
    statements = [
        {
            'action': ['*'],
            'principal': 'authenticated',
            'effect': 'allow',
            'condition': 'es_curso_propio',
        },
    ]

    def es_curso_propio(self, request, view, action) -> bool:
        persona = request.user.get_persona()

        try:
            curso = view.get_object()
        except Curso.DoesNotExist:
            return False

        # TODO: considerar docentes y ayudantes
        return EstudianteCurso.objects.filter(curso=curso, estudiante__persona=persona).exists()


class CursoIntegrantesView(RetrieveAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoIntegrantesSerializer
    permission_classes = [PoliticaIntegrantes | AdministradoresLeerEscribir, ]


class HistorialCursosView(ListAPIView):
    serializer_class = HistorialCursosSerializer
    permission_classes = [LeerInfoPropia | AdministradoresLeerEscribir, ]

    def get_queryset(self):
        persona = self.request.query_params.get('persona', None)

        cursos_inscritos = EstudianteCurso.objects.filter(
            estudiante__persona=persona
        ).order_by('curso__periodo')
        return cursos_inscritos


class OpcionesCursoView(APIView):
    permission_classes = [TodosSoloLeer, ]

    def get(self, request, format=None):
        data = {
            'roles': serializar_opciones(DocenteCurso.roles),
            'tipos_horario': serializar_opciones(Horario.tipos_horario),
            'dias': serializar_opciones(Horario.dias),
            'modulos': ModuloSerializer(Modulo.objects.all(), many=True).data,
        }

        return Response(data)


class CategoriaActividadViewSet(viewsets.ModelViewSet):
    queryset = CategoriaActividad.objects.all()
    serializer_class = CategoriaActividadSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir, ]


class CursosDocenteView(ListAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoHorarioSerializer
    permission_classes = [LeerInfoPropia | AdministradoresLeerEscribir, ]

    def get_queryset(self):
        queryset = super().get_queryset()

        persona = self.request.query_params.get('persona', None)
        if persona is not None:
            cursos = DocenteCurso.objects.filter(persona=persona).values('curso')
            queryset = queryset.filter(pk__in=cursos)

        periodo = self.request.query_params.get('periodo', None)
        if periodo is not None:
            queryset = queryset.filter(periodo=periodo)
        return queryset


class ActividadViewSet(viewsets.ModelViewSet):
    queryset = Actividad.objects.all()
    serializer_class = ActividadSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir, ]


class ActividadesCursoViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin, GenericViewSet, ):
    queryset = Curso.objects.all()
    serializer_class = ActividadesCursoSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response({
         'mensaje': "Las actividades se registraron con éxito"}, status=status.HTTP_201_CREATED)


class EvaluacionViewSet(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer
    permission_classes = [TodosSoloLeer | AdministradoresLeerEscribir, ]


class EvaluacionesActividadViewSet(mixins.RetrieveModelMixin,
                                   mixins.CreateModelMixin, GenericViewSet):
    queryset = Actividad.objects.all()
    serializer_class = EvaluacionesActividadSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        super().create(request, *args, **kwargs)
        return Response({
         'mensaje': "Las evaluaciones se registraron con éxito"}, status=status.HTTP_201_CREATED)


class EvaluacionesCursoViewset(ReadOnlyModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = EvaluacionesCursoSerializer
    permission_classes = [AllowAny]


class TestNotaViewset(viewsets.ModelViewSet):
    queryset = Nota.objects.all()
    serializer_class = NotaEvaluacionSerializer
    permission_classes = [AllowAny]


class NotasEvaluacionViewset(viewsets.ModelViewSet):
    queryset = Evaluacion.objects.all()
    serializer_class = EnvioNotasEvaluacionSerializer
    permission_classes = [AllowAny]


class CursoEstudiantesView(RetrieveAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoEstudiantesSerializer
    permission_classes = [AllowAny]


class NotasEstudianteCursoView(ListAPIView):
    queryset = Nota.objects.all()
    serializer_class = NotaEvaluacionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()

        persona = self.request.query_params.get('persona', None)
        curso = self.request.query_params.get('curso', None)
        if (persona is not None) and (curso is not None):

            estudiantecurso = EstudianteCurso.objects.filter(
                curso=curso)
            queryset = queryset.filter(estudiante_curso__in=estudiantecurso,
                                       estudiante_curso__estudiante__persona=persona)  # !!!
            print(queryset)
        return queryset


class ConfiguracionCursoView(RetrieveUpdateAPIView):
    queryset = Curso.objects.all()
    serializer_class = ConfiguracionCursoSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([AllowAny])
def calcular_notas_presentacion(request):

    curso_id = request.query_params.get('curso', None)
    curso = Curso.objects.get(pk=curso_id)
    estudiantes_curso = EstudianteCurso.objects.filter(curso=curso)

    for e in estudiantes_curso:
        e.get_nota_presentacion()

    cantidad_estudiantes = estudiantes_curso.count()
    notas_obtenidas = estudiantes_curso.filter(nota_presentacion__isnull=False)

    if notas_obtenidas.count() == cantidad_estudiantes:
        mensaje = "Éxito"
    else:
        mensaje = "No se pudo obtener todas las notas de presentación. Por favor verifique \
        que se hayan ingresado las notas de todas las evaluaciones."

    serializador = NotasPresentacionSerializer(data=estudiantes_curso, many=True)
    serializador.is_valid()
    return Response({
        'mensaje': mensaje,
        'notas': serializador.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def calcular_notas_finales(request):

    curso_id = request.query_params.get('curso', None)
    curso = Curso.objects.get(pk=curso_id)
    estudiantes_curso = EstudianteCurso.objects.filter(curso=curso)

    for e in estudiantes_curso:
        e.get_nota_final()

    if estudiantes_curso.filter(nota_final__isnull=True).exists():
        mensaje = "No se pudo obtener todas las notas finales. Por favor verifique \
        la configuración del curso y el ingreso de notas de exámen (si corresponden)"
    else:
        mensaje = "Éxito"

    serializador = NotasFinalesSerializer(data=estudiantes_curso, many=True)
    serializador.is_valid()
    return Response({
        'mensaje': mensaje,
        'notas': serializador.data}, status=status.HTTP_200_OK)


class NotasExamenViewset(GenericViewSet, ListModelMixin, UpdateModelMixin, RetrieveModelMixin):
    queryset = Curso.objects.all()
    serializer_class = NotasExamenCursoSerializer
    permission_classes = [AllowAny]


class VistaResumenCursoView(ReadOnlyModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = VistaResumenCursoSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
def notas_resumen_curso(request, curso):
    try:
        curso = Curso.objects.get(pk=curso)
    except Curso.DoesNotExist:
        return Response(
            {'mensaje': 'No se encontró el curso ingresado.'},
            status=status.HTTP_400_BAD_REQUEST)

    actividades = Actividad.objects.filter(curso=curso)
    evaluaciones = Evaluacion.objects.filter(actividad__in=actividades)
    notas = Nota.objects.filter(evaluacion__in=evaluaciones)
    serializador_notas = NotaEvaluacionSerializer(notas, many=True)

    notas_estudiantecurso = EstudianteCurso.objects.filter(curso=curso)
    serializador_estudiantecurso = NotasVistaResumenSerializer(notas_estudiantecurso, many=True)

    return Response({
        'notas': serializador_notas.data,
        'estudiantecursos': serializador_estudiantecurso.data})
