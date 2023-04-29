from django.contrib.auth.models import Group

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import AccessToken

from persona.permisos import GRUPOS

from persona.models import Estudiante, EstadoEstudiante

from matricula.models import (
    ProcesoMatricula, PeriodoProcesoMatricula, PostulanteDefinitivo,
    ValorMatricula, GratuidadEstudiante, MatriculaEstudiante, ArancelEstudiante,
    ValorArancel, TNEEstudiante, EstudianteRespondeEncuesta,
)
from matricula.serializers import PostulanteDefinitivoSerializer


def info_login_postulante(postulantes, token=None):
    postulante = None

    habilitados = postulantes.filter(habilitado=True)
    if habilitados.exists():
        postulante = habilitados.first()

        # chequear que existe un periodo abierto
        if not PeriodoProcesoMatricula.hay_periodo_abierto(publico=0) \
                and not postulante.completo_proceso():
            return Response(
                {'mensaje': 'Lo sentimos, no existe un periodo de matrícula abierto.'},
                status=status.HTTP_400_BAD_REQUEST)

    else:
        for post in postulantes:
            if post.completo_proceso():
                postulante = post
                break

    if postulante is None:
        return Response(
            {'mensaje': f'Lo sentimos, actualmente no estás habilitado(a) para matricularte.'
                f' Si estás en lista de espera y pasas a ser seleccionado(a) te contactaremos.'},
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
        access_token = AccessToken.for_user(postulante.persona.user)

    return Response({
        'postulante': PostulanteDefinitivoSerializer(postulante).data,
        'accessToken': str(access_token),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_postulantes(request):
    if 'rut' not in request.data or 'numero_demre' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar un rut y número DEMRE.'},
            status=status.HTTP_400_BAD_REQUEST)

    numero_documento = request.data['rut'].split('-')[0]
    numero_demre = request.data['numero_demre']
    proceso = ProcesoMatricula.objects.get(activo=True)

    # chequear que existen postulaciones asociadas
    postulantes = PostulanteDefinitivo.objects.filter(
        proceso_matricula=proceso,
        persona__numero_documento=numero_documento
    )
    if not postulantes:
        return Response(
            {'mensaje': 'Lo sentimos, el rut ingresado no está registrado en nuestro sistema.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear contraseña
    postulantes = postulantes.filter(numero_demre=numero_demre)
    if not postulantes.exists():
        return Response(
            {'mensaje': 'El usuario o la contraseña son incorrectos, intente nuevamente.'},
            status=status.HTTP_400_BAD_REQUEST)

    return info_login_postulante(postulantes)


@api_view(['POST'])
@permission_classes([AllowAny])
def validar_token_postulantes(request):
    if 'postulante' not in request.data or 'token' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar un id de postulante y un token.'},
            status=status.HTTP_400_BAD_REQUEST)

    postulante_id = request.data['postulante']
    token = request.data['token']

    # chequear que existe el postulante
    postulantes = PostulanteDefinitivo.objects.filter(id=postulante_id)
    if not postulantes.exists():
        return Response(
            {'mensaje': 'El postulante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    return info_login_postulante(postulantes, token)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aceptar_vacante(request):
    if 'postulante' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar un id de postulante.'},
            status=status.HTTP_400_BAD_REQUEST)

    postulante_id = request.data['postulante']

    # chequear que existe el postulante enviado
    try:
        postulante = PostulanteDefinitivo.objects.get(id=postulante_id)
    except PostulanteDefinitivo.DoesNotExist:
        return Response(
            {'mensaje': 'El postulante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que el postulante corresponde al usuario actual
    if request.user.persona != postulante.persona:
        return Response(
            {'mensaje': 'Solo el postulante puede aceptar su vacante.'},
            status=status.HTTP_400_BAD_REQUEST)

    if not PeriodoProcesoMatricula.hay_periodo_abierto(publico=0):
        return Response(
            {'mensaje': 'Lo sentimos, no existe un periodo de matrícula abierto.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que el postulante sigue habilitado
    if not postulante.habilitado:
        return Response(
            {'mensaje': 'Lo sentimos, ya no te encuentras habilitado para matricularte.'},
            status=status.HTTP_400_BAD_REQUEST)

    if postulante.acepta_vacante:
        return Response({
            'estudiante': postulante.estudiante.id,
        })

    proceso = postulante.proceso_matricula
    periodo_ingreso_uaysen = postulante.persona.periodo_ingreso_uaysen()
    if periodo_ingreso_uaysen is None:
        periodo_ingreso_uaysen = proceso.periodo_ingreso

    # crear estudiante asociado
    estudiante = Estudiante(
        plan=postulante.plan,
        persona=postulante.persona,
        via_ingreso=postulante.via_ingreso,
        periodo_ingreso=proceso.periodo_ingreso,
        periodo_ingreso_uaysen=periodo_ingreso_uaysen,
        estado_estudiante=EstadoEstudiante.objects.get(id=6),  # matrícula pendiente
    )
    estudiante.save()
    grupo_estudiantes = Group.objects.get(name=GRUPOS.ESTUDIANTES)
    estudiante.persona.user.groups.add(grupo_estudiantes)

    postulante.acepta_vacante = True
    postulante.estudiante = estudiante
    postulante.save()

    # registrar etapa actual del estudiante
    estudiante.registrar_etapa_matricula(etapa=1)

    # crear GratuidadEstudiante
    gratuidad = GratuidadEstudiante(
        proceso_matricula=proceso,
        estudiante=estudiante,
        tiene_gratuidad=postulante.preseleccionado_gratuidad
    )
    gratuidad.save()

    # crear MatriculaEstudiante
    valor_matricula = ValorMatricula.objects.get(
        proceso_matricula=proceso,
        plan=estudiante.plan,
    )
    matricula = MatriculaEstudiante(
        proceso_matricula=proceso,
        estudiante=estudiante,
        monto_final=valor_matricula.valor
    )
    # preseleccionados gratuidad
    if postulante.preseleccionado_gratuidad:
        matricula.monto_final = 0
        matricula.tiene_beneficios = True
        matricula.beneficios_monto_total = valor_matricula.valor
        matricula.descripcion_beneficios = '¡Felicidades! Has obtenido el beneficio de la' \
            + ' gratuidad por lo que el costo de tu matrícula y arancel es de $0.'

    matricula.save()

    # crear ArancelEstudiante
    valor_plan = ValorArancel.objects.get(
        proceso_matricula=proceso,
        plan=postulante.plan
    )
    arancel = ArancelEstudiante(
        proceso_matricula=proceso,
        estudiante=estudiante,
        valor_arancel=valor_plan,
        monto=valor_plan.valor,
    )

    # preseleccionados gratuidad
    if postulante.preseleccionado_gratuidad:
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

    return Response({
        'estudiante': estudiante.id,
    })
