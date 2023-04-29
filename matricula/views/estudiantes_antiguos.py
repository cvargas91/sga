from google.auth import jwt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView

from rest_framework_simplejwt.tokens import AccessToken

from persona.permisos import AdministradoresLeerEscribir
from persona.views import flow

from persona.models import Estudiante

from matricula.models import (
    ProcesoMatricula, PeriodoProcesoMatricula,
    ValorMatricula, GratuidadEstudiante, MatriculaEstudiante, ArancelEstudiante,
    InhabilitantesMatricula, ValorArancel, TNEEstudiante, EstudianteRespondeEncuesta,
)
from matricula.serializers import EstudianteAntiguoSerializer, InhabilitantesMatriculaSerializer

from .comunes import PoliticaDatosEstudiante


def info_login_estudiante_antiguo(estudiante, token=None):
    proceso_matricula = ProcesoMatricula.objects.get(activo=True)

    # chequear si el postulante completó el proceso
    etapa_actual = estudiante.etapa_estudiante()
    try:
        matricula = MatriculaEstudiante.objects.get(
            proceso_matricula=proceso_matricula,
            estudiante=estudiante
        )
        matricula_valida = matricula.estado == 1

    except MatriculaEstudiante.DoesNotExist:
        matricula_valida = False

    # permitir acceder a estudiantes que hayan completado el proceso
    if not (etapa_actual >= 4 and matricula_valida):

        # chequear que existe un periodo para estudiantes antiguos abierto
        if not PeriodoProcesoMatricula.hay_periodo_abierto(publico=1):
            return Response(
                {'mensaje': 'Lo sentimos, no existe un periodo de matrícula abierto.'},
                status=status.HTTP_400_BAD_REQUEST)

    # retornar token
    if token is not None:
        try:
            access_token = AccessToken(token=token)
        except Exception:
            return Response(
                {'mensaje': 'El token no es valido o ya expiró.'},
                status=status.HTTP_400_BAD_REQUEST)

    else:
        access_token = AccessToken.for_user(estudiante.persona.user)

    return Response({
        'estudiante': EstudianteAntiguoSerializer(estudiante).data,
        'accessToken': str(access_token),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_estudiantes_antiguos(request):
    if 'jwt' not in request.data:
        return Response(
            {'mensaje': 'Debe enviar un JSON Web Token para validación'},
            status=status.HTTP_400_BAD_REQUEST)

    payload = jwt.decode(request.data.get('jwt'), verify=False)
    email = payload['email']
    proceso_matricula = ProcesoMatricula.objects.get(activo=True)

    estudiantes_antiguos = Estudiante.objects.exclude(
        periodo_ingreso=proceso_matricula.periodo_ingreso,
    ).filter(
        estado_estudiante_id__in=[4, 1],  # regular o congelado
    )
    estudiantes_transferencia_interna = Estudiante.objects.filter(
        periodo_ingreso=proceso_matricula.periodo_ingreso,
        via_ingreso=7,  # transferencia interna
    )
    candidatos = estudiantes_antiguos | estudiantes_transferencia_interna

    # encontrar usuario asociado
    candidatos = candidatos.filter(persona__mail_institucional=email)
    if not candidatos.exists():
        return Response(
            {'mensaje': 'Lo sentimos, el correo utilizado no está asociado a un estudiante.'},
            status=status.HTTP_400_BAD_REQUEST)

    estudiante = candidatos.first()

    if estudiante.habilitado is False:
        return Response(
            {'mensaje': 'Estudiante se encuentra inhabilitado/a.'},
            status=status.HTTP_400_BAD_REQUEST)

    return info_login_estudiante_antiguo(estudiante)


@api_view(['POST'])
@permission_classes([AllowAny])
def validar_token_estudiantes_antiguos(request):
    if 'estudiante' not in request.data or 'token' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar un id de estudiante y un token.'},
            status=status.HTTP_400_BAD_REQUEST)

    estudiante_id = request.data['estudiante']
    token = request.data['token']

    # chequear que existe el estudiante
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except Estudiante.DoesNotExist:
        return Response(
            {'mensaje': 'El estudiante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    return info_login_estudiante_antiguo(estudiante, token)


class InhabilitantesMatriculaView(RetrieveAPIView):
    serializer_class = InhabilitantesMatriculaSerializer
    permission_classes = [PoliticaDatosEstudiante | AdministradoresLeerEscribir, ]

    def get_object(self):
        # esta vista recibe un id de estudiante y retorna sus inhabilitantes del proceso activo
        estudiante = Estudiante.objects.get(id=self.kwargs['estudiante_id'])

        return InhabilitantesMatricula.objects.get(
            proceso_matricula__activo=True,
            estudiante=estudiante,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def comenzar_proceso_estudiante_antiguo(request):
    if 'estudiante' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar un id de estudiante.'},
            status=status.HTTP_400_BAD_REQUEST)

    estudiante_id = request.data['estudiante']

    # chequear que existe el estudiante enviado
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except Estudiante.DoesNotExist:
        return Response(
            {'mensaje': 'El estudiante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que el estudiante corresponde al usuario actual
    if request.user.persona != estudiante.persona:
        return Response(
            {'mensaje': 'Solo el estudiante puede aceptar su vacante.'},
            status=status.HTTP_400_BAD_REQUEST)

    if not PeriodoProcesoMatricula.hay_periodo_abierto(publico=1):
        return Response(
            {'mensaje': 'Lo sentimos, no existe un periodo de matrícula abierto.'},
            status=status.HTTP_400_BAD_REQUEST)

    proceso = ProcesoMatricula.objects.get(activo=True)

    # chequear inhabilitantes
    inhabilitantes = InhabilitantesMatricula.objects.get(
        proceso_matricula=proceso, estudiante=estudiante)

    if inhabilitantes.tiene_deuda_finanzas or inhabilitantes.tiene_deuda_biblioteca:
        return Response(
            {'mensaje': 'El estudiante posee deudas pendientes.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear GratuidadEstudiante
    gratuidad = GratuidadEstudiante.objects.get(
        proceso_matricula=proceso,
        estudiante=estudiante
    )

    # registrar etapa actual del estudiante
    estudiante.registrar_etapa_matricula(etapa=1)

    # crear MatriculaEstudiante
    valor_matricula = ValorMatricula.objects.get(
        proceso_matricula=proceso,
        plan=estudiante.plan,
    )
    matricula = MatriculaEstudiante(
        proceso_matricula=proceso,
        estudiante=estudiante,
        monto_final=valor_matricula.valor,
    )
    # preseleccionados gratuidad
    if gratuidad.tiene_gratuidad:
        matricula.monto_final = 0
        matricula.tiene_beneficios = True
        matricula.beneficios_monto_total = valor_matricula.valor
        matricula.descripcion_beneficios = '¡Felicidades! Has obtenido el beneficio de la' \
            + ' gratuidad por lo que el costo de tu matrícula y arancel es de $0.'

    matricula.save()

    # crear ArancelEstudiante
    valor_plan = ValorArancel.objects.get(
        proceso_matricula=proceso,
        plan=estudiante.plan,
    )
    arancel = ArancelEstudiante(
        proceso_matricula=proceso,
        estudiante=estudiante,
        valor_arancel=valor_plan,
        monto=valor_plan.valor,
    )

    # preseleccionados gratuidad
    if gratuidad.tiene_gratuidad:
        arancel.monto = 0
        arancel.tiene_beneficios = True
        arancel.beneficios_monto_total = valor_plan.valor
        arancel.descripcion_beneficios = '¡Felicidades! Has obtenido el beneficio de la' \
            + ' gratuidad por lo que el costo de tu matrícula y arancel es de $0.'

    arancel.save()

    # crear TNEEstudiante
    tne = TNEEstudiante(proceso_matricula=proceso, estudiante=estudiante)
    tne.save()

    # crear EstudianteRespondeEncuesta
    encuesta = EstudianteRespondeEncuesta(proceso_matricula=proceso, estudiante=estudiante)
    encuesta.save()

    return Response({'estudiante': estudiante.id})
