from rest_framework.generics import ListAPIView

from rest_access_policy import AccessPolicy

from matricula.models import MatriculaEstudiante, EstudianteRespondeEncuesta
from persona.models import Persona

from .serializers import PersonaUcampusSerializer, MatriculaUcampusSerializer


class PermisoUcampus(AccessPolicy):
    statements = [
        {
            'action': ['<safe_methods>'],
            'principal': ['group:ucampus', 'admin'],
            'effect': 'allow',
        },
    ]


class PersonaUcampusView(ListAPIView):
    queryset = Persona.objects.all()
    serializer_class = PersonaUcampusSerializer
    permission_classes = [PermisoUcampus, ]

    def get_queryset(self):
        # filtrar solo las personas que son estudiantes
        queryset = super().get_queryset().exclude(estudiantes=None)

        rut = self.request.query_params.get('rut', None)
        if rut is not None:
            queryset = queryset.filter(numero_documento__in=rut.split(','))

        return queryset


class MatriculaUcampusView(ListAPIView):
    queryset = MatriculaEstudiante.objects.prefetch_related(
        'estudiante__persona',
        'estudiante__plan__carrera',
        'estudiante__via_ingreso',
        'estudiante__periodo_ingreso',
        'proceso_matricula'
    )
    serializer_class = MatriculaUcampusSerializer
    permission_classes = [PermisoUcampus, ]

    def get_queryset(self):
        # filtrar estudiantes que hayan respondido la encuesta de caracterización
        respondieron_encuesta = EstudianteRespondeEncuesta.objects.filter(
            proceso_matricula__activo=True,
            responde_encuesta=True,
        ).values_list('estudiante')
        queryset = self.queryset.filter(
            proceso_matricula__activo=True,
            estado=1,
            estudiante__in=respondieron_encuesta,
        )

        rut = self.request.query_params.get('rut', None)
        if rut is not None:
            queryset = queryset.filter(estudiante__persona__numero_documento__in=rut.split(','))

        return queryset


class MatriculaHistoricaUcampusView(MatriculaUcampusView):
    def get_queryset(self):
        queryset = self.queryset.all()

        rut = self.request.query_params.get('rut', None)
        if rut is not None:
            queryset = queryset.filter(estudiante__persona__numero_documento__in=rut.split(','))

        anio = self.request.query_params.get('año', None)
        if anio is not None:
            queryset = queryset.filter(proceso_matricula__ano=anio)

        return queryset
