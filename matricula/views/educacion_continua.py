from django.contrib.auth.models import Group

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import AccessToken

from persona.models import Estudiante, EstadoEstudiante
from persona.permisos import GRUPOS

from matricula.models import (
    ProcesoMatricula, PeriodoProcesoMatricula,
    ValorMatricula, MatriculaEstudiante, ArancelEstudiante,
    ValorArancel, TNEEstudiante, EstudianteRespondeEncuesta,
    PostulanteEducacionContinua,
)
from matricula.serializers import PostulanteEducacionContinuaSerializer


def info_login_educacion_continua(postulante, token=None):
    # chequear si el postulante completó el proceso
    etapa_actual = postulante.etapa_actual()
    matricula_valida = False
    if postulante.estudiante:
        matricula = MatriculaEstudiante.objects.get(
            proceso_matricula=postulante.proceso_matricula,
            estudiante=postulante.estudiante
        )
        matricula_valida = matricula.estado == 1

    # permitir acceder a postulantes que hayan completado el proceso
    if not (etapa_actual >= 4 and matricula_valida):

        # chequear que existe un periodo para educación continua abierto
        if not PeriodoProcesoMatricula.hay_periodo_abierto(publico=2, plan=postulante.plan):
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
        access_token = AccessToken.for_user(postulante.persona.user)

    return Response({
        'postulante': PostulanteEducacionContinuaSerializer(postulante).data,
        'accessToken': str(access_token),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def login_educacion_continua(request):
    if 'rut' not in request.data or 'clave' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar un rut y clave secreta.'},
            status=status.HTTP_400_BAD_REQUEST)

    numero_documento = request.data['rut'].split('-')[0]
    clave = request.data['clave']
    proceso = ProcesoMatricula.objects.get(activo=True)

    # chequear que existen postulaciones asociadas
    postulantes = PostulanteEducacionContinua.objects.filter(
        proceso_matricula=proceso,
        persona__numero_documento=numero_documento
    )
    if not postulantes.exists():
        return Response(
            {'mensaje': 'Lo sentimos, el rut ingresado no está registrado en nuestro sistema.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear contraseña
    postulantes = postulantes.filter(clave=clave)
    if not postulantes.exists():
        return Response(
            {'mensaje': 'El usuario o la clave son incorrectos, intente nuevamente.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear estado
    postulantes = postulantes.exclude(habilitado=False)
    if not postulantes.exists():
        return Response(
            {'mensaje': f'Lo sentimos, actualmente no estás habilitado(a) para matricularte.'
                f' Si estás en lista de espera y pasas a ser seleccionado(a) te contactaremos.'},
            status=status.HTTP_400_BAD_REQUEST)

    # priorizar planes que tienen un periodo activo actualmente
    planes = PeriodoProcesoMatricula.periodos_abiertos(publico=2) \
        .values_list('planes', flat=True).distinct()

    if planes and postulantes.filter(plan__in=planes).exists():
        postulantes = postulantes.filter(plan__in=planes)

    return info_login_educacion_continua(postulantes.first())


@api_view(['POST'])
@permission_classes([AllowAny])
def validar_token_educacion_continua(request):
    if 'postulante' not in request.data or 'token' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar un id de postulante y un token.'},
            status=status.HTTP_400_BAD_REQUEST)

    postulante_id = request.data['postulante']

    # chequear que existe el postulante
    try:
        postulante = PostulanteEducacionContinua.objects.get(id=postulante_id)
    except PostulanteEducacionContinua.DoesNotExist:
        return Response(
            {'mensaje': 'El postulante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que el postulante sigue habilitado
    if not postulante.habilitado:
        return Response(
            {'mensaje': 'Lo sentimos, ya no te encuentras habilitado(a) para matricularte.'},
            status=status.HTTP_400_BAD_REQUEST)

    return info_login_educacion_continua(postulante, token=request.data['token'])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aceptar_vacante_educacion_continua(request):
    if 'postulante' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar un id de postulante.'},
            status=status.HTTP_400_BAD_REQUEST)

    postulante_id = request.data['postulante']

    # chequear que existe el postulante enviado
    try:
        postulante = PostulanteEducacionContinua.objects.get(id=postulante_id)
    except PostulanteEducacionContinua.DoesNotExist:
        return Response(
            {'mensaje': 'El postulante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que el postulante corresponde al usuario actual
    if request.user.persona != postulante.persona:
        return Response(
            {'mensaje': 'Solo el postulante puede aceptar su vacante.'},
            status=status.HTTP_400_BAD_REQUEST)

    # chequear que existe un periodo para educación continua abierto
    if not PeriodoProcesoMatricula.hay_periodo_abierto(publico=2, plan=postulante.plan):
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

    # calcular descuentos matricula
    if postulante.tipo_descuento_matricula is not None:
        matricula.tiene_beneficios = True

        if postulante.tipo_descuento_matricula == 0:  # monto fijo
            descuento = postulante.monto_descuento_matricula

        elif postulante.tipo_descuento_matricula == 1:  # porcentaje
            # TODO: regla de redondeo
            descuento = postulante.monto_descuento_matricula / 100.0 * valor_matricula.valor

        matricula.beneficios_monto_total = descuento
        matricula.monto_final = valor_matricula.valor - descuento
        matricula.descripcion_beneficios = postulante.descripcion_descuento_matricula

    matricula.save()

    # crear TNEEstudiante
    tne = TNEEstudiante(proceso_matricula=proceso, estudiante=estudiante)
    tne.save()

    # crear ArancelEstudiante
    valor_plan = ValorArancel.objects.get(proceso_matricula=proceso, plan=postulante.plan)
    arancel = ArancelEstudiante(
        proceso_matricula=proceso,
        estudiante=estudiante,
        valor_arancel=valor_plan,
        monto=valor_plan.valor,
    )

    # calcular descuentos arancel
    if postulante.tipo_descuento_arancel is not None:
        arancel.tiene_beneficios = True

        if postulante.tipo_descuento_arancel == 0:  # monto fijo
            descuento = postulante.monto_descuento_arancel

        elif postulante.tipo_descuento_arancel == 1:  # porcentaje
            # TODO: regla de redondeo
            descuento = postulante.monto_descuento_arancel / 100.0 * valor_plan.valor

        arancel.beneficios_monto_total = descuento
        arancel.monto = valor_plan.valor - descuento
        arancel.descripcion_beneficios = postulante.descripcion_descuento_arancel

    arancel.save()

    # crear EstudianteRespondeEncuesta
    encuesta = EstudianteRespondeEncuesta(proceso_matricula=proceso, estudiante=estudiante)
    encuesta.save()

    return Response({
        'estudiante': estudiante.id,
    })
