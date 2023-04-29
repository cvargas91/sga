from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes

# transbank webpay plus
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType

from matricula.models import (
    ProcesoMatricula, MatriculaEstudiante, ArancelEstudiante, PeriodoProcesoMatricula,
    ValorMatricula, ValorArancel,
)

from persona.models import Estudiante

from .models import (
    Productos, FormaPago, OrdenCompra, OrdenCompraDetalle, PagoWebPay,
)


# configuración de producción para webpay, mover a archivo de ambiente
CONF_WEBPAY = WebpayOptions(
    settings.WEBPAY_CODIGO_COMERCIO,
    settings.WEBPAY_API_KEY,
    getattr(IntegrationType, settings.WEBPAY_TIPO_INTEGRACION)
)


def generar_pago_webpay(orden_compra: OrdenCompra, monto: int, url_redireccion: str):
    # se envia a webpay el id de la orden de compra
    buy_order = orden_compra.id

    return_url = f'{settings.URL_BACKEND}{url_redireccion}'

    # campo compuesto porque sistema no maneja session
    session_id = 'sesion_' + str(orden_compra.id)
    transaction = Transaction.create(buy_order, session_id, monto, return_url, CONF_WEBPAY)

    pago_webpay = PagoWebPay(
        orden_compra=orden_compra,
        token=transaction.token,
        url_redirection=transaction.url,
        buy_order=buy_order,
        session_id=session_id,
        amount=monto
    )
    pago_webpay.save()

    # Actualizo campos de la orden de compra referentes a webpay
    orden_compra.id_sesion = session_id
    orden_compra.token_webpay = transaction.token
    orden_compra.save()

    return Response({
        'url_redirect': transaction.url,
        'token_webpay': transaction.token,
    })


@api_view(['POST', ])
@permission_classes([IsAuthenticated])
def pago_matricula(request):
    """ API Nº1 para crear orden de compra matrícula """
    # Códigos para forma_pago_id que vendrían del request (API):
    # 1 - caja
    # 2 - efectivo
    # 3 - cheque
    # 4 - red_compra
    # 5 - transferencia_bancaria
    # 6 - deposito_bancario
    # 7 - webpay

    if 'estudiante_id' not in request.data or 'forma_pago_id' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar estudiante_id, forma_pago_id.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    estudiante_id = request.data['estudiante_id']
    forma_pago_id = request.data['forma_pago_id']

    # chequear que existe el estudiante
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except ObjectDoesNotExist:
        return Response(
            {'mensaje': 'El estudiante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # chequear que el estudiante corresponde al usuario actual
    if request.user.persona != estudiante.persona:
        return Response(
            {'mensaje': 'Solo el estudiante puede elegir su forma de pago.'},
            status=status.HTTP_400_BAD_REQUEST)

    if not estudiante.habilitado_matricula():
        return Response(
            {'mensaje': 'Lo sentimos, ya no te encuentras habilitado para matricularte.'},
            status=status.HTTP_400_BAD_REQUEST)

    # Buscar valor matricula según proceso
    proceso_matricula = ProcesoMatricula.objects.get(activo=True)
    matricula_estudiante = MatriculaEstudiante.objects.get(
        estudiante=estudiante, proceso_matricula=proceso_matricula)

    # chequear que no exista una orden de compra pagada
    if matricula_estudiante.orden_compra and matricula_estudiante.orden_compra.estado_pago == 1:
        return Response(
            {'mensaje': 'Ya existe una orden de compra aprobada para tu matrícula.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    periodos_abiertos = PeriodoProcesoMatricula.periodos_abiertos(
        publico=estudiante.tipo_estudiante(), plan=estudiante.plan
    )
    if not periodos_abiertos.exists():
        return Response(
            {'mensaje':
                'No puedes modificar tu forma de pago si no hay un periodo de matrícula abierto.'},
            status=status.HTTP_400_BAD_REQUEST)

    # cancelar orden de compra anterior
    if matricula_estudiante.orden_compra:
        matricula_estudiante.orden_compra.estado_pago = 4
        matricula_estudiante.orden_compra.save()

    # se obtiene monto matricula y suma al monto total
    monto_final = matricula_estudiante.monto_final
    monto_descuentos = matricula_estudiante.beneficios_monto_total

    # forzar forma de pago caja para ordenes de compra "gratis"
    if monto_final == 0:
        forma_pago_id = 1

    # crear orden de compra con datos de estudiante
    orden_compra = OrdenCompra(
        persona=estudiante.persona,
        monto_total=monto_final + monto_descuentos,
        total_descuento_beneficios=monto_descuentos,
        forma_pago=FormaPago.objects.get(id=forma_pago_id),
        ip=get_client_ip(request),
        estado_pago=0,  # se crea la orden de compra con estado pendiente (para todos los casos)
        estado=0,  # 0: al crearse y 1 al cambiar de estados_pago pendiente (inicial) pasa a 1
    )
    orden_compra.save()

    if monto_final == 0:
        orden_compra.validar()
        matricula_estudiante.validar()

    # guardar orden de compra actual
    matricula_estudiante.orden_compra = orden_compra
    matricula_estudiante.periodo_matricula = periodos_abiertos.first()
    matricula_estudiante.save()

    # crear orden de compra detalle con productos asociados al pago
    valor_matricula = ValorMatricula.objects.get(
        proceso_matricula=proceso_matricula, plan=estudiante.plan)

    orden_compra_detalle = OrdenCompraDetalle(
        orden_compra=orden_compra,
        producto=valor_matricula.producto,
        valor=valor_matricula.producto.valor,
        cantidad=1,
        descuento=0  # TODO: actualizar para gratuidad
    )
    orden_compra_detalle.save()

    # webpay
    if forma_pago_id == 7:
        return generar_pago_webpay(
            orden_compra=orden_compra,
            monto=monto_final,
            url_redireccion=reverse('resultado-pago-matricula'),
        )

    # registrar etapa actual del estudiante
    estudiante.registrar_etapa_matricula(etapa=3)

    # Para todas las formas de pago que no sean webpay
    return Response({
        'OK': True,
    })


@api_view(['POST', ])
@permission_classes([IsAuthenticated])
def pago_arancel(request):
    """ API Nº2 para crear orden de compra arancel """

    # Códigos para forma_pago_id que vendrían del request (API):
    # 1 - caja
    # 2 - efectivo
    # 3 - cheque
    # 4 - red_compra
    # 5 - transferencia_bancaria
    # 6 - deposito_bancario
    # 7 - webpay

    # Códigos para estados de la orden de compra:
    # 0 - Pendiente de pago (Cuando es creada)
    # 1 - Pagada/Cerrada (en todas sus formas de pago)
    # 2 - Rechazada (diversos casos: caída internet, cierre navegador, etc)
    # 3 - Anulada por retracto webpay ("REFUND": devolución del dinero hasta 1 hr posterior al pago)
    # 4 - Cancelada por cambio en forma de pago (Estado proveniente desde mantenedor)

    if 'estudiante_id' not in request.data or 'forma_pago_id' not in request.data:
        return Response(
            {'mensaje': 'Debe ingresar estudiante_id, forma_pago_id.'},
            status=status.HTTP_400_BAD_REQUEST)

    # Variables para pruebas de API
    estudiante_id = request.data['estudiante_id']
    forma_pago_id = request.data['forma_pago_id']

    # chequear que existe la persona
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except ObjectDoesNotExist:
        return Response(
            {'mensaje': 'El estudiante solicitado no existe.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # chequear que el estudiante corresponde al usuario actual
    if request.user.persona != estudiante.persona:
        return Response(
            {'mensaje': 'Solo el estudiante puede elegir su forma de pago.'},
            status=status.HTTP_400_BAD_REQUEST)

    if not estudiante.habilitado_matricula():
        return Response(
            {'mensaje': 'Lo sentimos, ya no te encuentras habilitado para matricularte.'},
            status=status.HTTP_400_BAD_REQUEST)

    # obtener valor arancel según proceso (año)
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

    # se obtiene monto arancel
    monto_arancel = arancel_estudiante.monto + arancel_estudiante.beneficios_monto_total

    # calcular descuento oportuno
    periodo = periodos_abiertos.first()
    dcto = periodo.dcto_oportuno / 100.0
    descuentos = int(arancel_estudiante.beneficios_monto_total + dcto * arancel_estudiante.monto)

    # forzar forma de pago caja para ordenes de compra con monto total 0
    if monto_arancel - descuentos == 0:
        forma_pago_id = 1

    # crear orden de compra con datos de estudiante
    orden_compra = OrdenCompra(
        persona=estudiante.persona,
        forma_pago=FormaPago.objects.get(id=forma_pago_id),
        ip=get_client_ip(request),
        monto_total=monto_arancel,
        total_descuento_beneficios=descuentos,
        estado_pago=0,  # se crea la orden de compra con estado pendiente (para todos los casos)
        estado=0,  # 0: al crearse y 1 al cambiar de estados_pago pendiente (inicial) pasa a 1
    )
    orden_compra.save()

    # guardar orden de compra actual
    arancel_estudiante.orden_compra = orden_compra
    arancel_estudiante.pagare = None
    arancel_estudiante.pago_cuotas = False
    arancel_estudiante.periodo_matricula = periodo
    arancel_estudiante.save()

    # crear orden de compra detalle con productos asociados al pago
    valor_arancel = ValorArancel.objects.get(
        proceso_matricula=proceso_matricula, plan=estudiante.plan)
    orden_compra_detalle = OrdenCompraDetalle(
        orden_compra=orden_compra,
        producto=valor_arancel.producto,
        valor=valor_arancel.valor,
        cantidad=1,
        descuento=descuentos,
    )
    orden_compra_detalle.save()

    # registrar como pagadas ordenes con monto total 0
    if orden_compra.monto_a_pagar() == 0:
        orden_compra.validar()
        # arancel_estudiante.validar()

    # webpay
    if forma_pago_id == 7:
        return generar_pago_webpay(
            orden_compra=orden_compra,
            monto=monto_arancel - descuentos,
            url_redireccion=reverse('resultado-pago-arancel'),
        )

    # registrar etapa actual del estudiante
    estudiante.registrar_etapa_matricula(etapa=4)

    # para todas las formas de pago que no sean webpay
    return Response({
        'OK': True
    })


def resultado_pago_webpay(request):
    """
    Método para recibir resultado desde webpay y almacenar el resultado de la transacción en la
    base de datos

    retorna
    - si la compra fue aprobada o no
    - la orden de compra asociada a este pago
    """

    if 'TBK_TOKEN' not in request.data:
        token_webpay = request.query_params['token_ws']

        # se aplican los cambios a la API-REST
        response = Transaction.commit(token_webpay, CONF_WEBPAY)
        pago_webpay = PagoWebPay.objects.get(token=token_webpay)
        pago_webpay.completar(response)

        # Obtener OrdenCompra desde el modelo y actualizo
        orden_compra = OrdenCompra.objects.get(id=pago_webpay.buy_order, token_webpay=token_webpay)

        # chequear estado pago
        if pago_webpay.response_code == 0:
            orden_compra.validar()
            return True, orden_compra

        else:
            orden_compra.rechazar()
            return False, orden_compra

    # resultado con caso de error (cancelar/rechazo)
    pago_webpay = PagoWebPay.objects.get(token=request.data['TBK_TOKEN'])
    pago_webpay.rechazar(request.data['TBK_ORDEN_COMPRA'])
    return False, orden_compra


@api_view(['GET', ])
@permission_classes([AllowAny])
def resultado_pago_matricula(request):
    pago_aprobado, orden_compra = resultado_pago_webpay(request)

    # pago exítoso
    if pago_aprobado:
        # marcar matrícula válida
        matricula_estudiante = MatriculaEstudiante.objects.get(orden_compra=orden_compra)

        matricula_estudiante.validar()
        matricula_estudiante.estudiante.registrar_etapa_matricula(etapa=3)

    # redirect > hacia el frontend: url "/estado-pago-matricula/"
    return HttpResponseRedirect(f'{settings.URL_FRONTEND_MATRICULA}/estado-pago-matricula/')


@api_view(['GET', ])
@permission_classes([AllowAny])
def resultado_pago_arancel(request):
    pago_aprobado, orden_compra = resultado_pago_webpay(request)

    # pago exítoso
    if pago_aprobado:
        # registrar etapa actual del estudiante
        arancel_estudiante = ArancelEstudiante.objects.get(orden_compra=orden_compra)
        # arancel_estudiante.validar()
        arancel_estudiante.estudiante.registrar_etapa_matricula(etapa=4)

    # redirect > hacia el frontend: url "/estado-pago-arancel/"
    return HttpResponseRedirect(f'{settings.URL_FRONTEND_MATRICULA}/estado-pago-arancel/')


def estado_pago_webpay(orden_compra: OrdenCompra, producto: str):
    # Obtener pago_webpay de la orden de compra asociada
    try:
        pago_webpay = PagoWebPay.objects.get(orden_compra=orden_compra)
    except ObjectDoesNotExist:
        return Response(
            {'mensaje': 'No existe un pago webpay asociado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    estado = ''
    mensaje = ''
    comprobante_pago = ''

    if pago_webpay.response_code == 0:
        estado = 'OK'
        mensaje = f'Su pago de {producto} a través de webpay se ha realizado exitosamente'

        # Obtener productos de esta compra
        productos_ids = OrdenCompraDetalle.objects.filter(
            orden_compra=orden_compra
        ).values_list('producto')
        nombres_productos = Productos.objects.filter(
            id__in=productos_ids).values_list('nombre', flat=True)

        # Preparación data comrpobante pago
        comprobante_pago = {
            'buy_order': pago_webpay.buy_order,
            'monto': pago_webpay.amount,
            'authorization_code': pago_webpay.authorization_code,
            'transaction_date': pago_webpay.transaction_date,
            'payment_type_code': pago_webpay.payment_type_code,
            'tipo_cuota': '',  # Tipo de cuota
            'installments_number': pago_webpay.installments_number,
            'installments_amount': pago_webpay.installments_amount,
            'card_number': pago_webpay.card_number,
            'productos': nombres_productos
        }

    if pago_webpay.response_code == -1:
        estado = 'Error'
        mensaje = 'Transacción Rechazada: error en el ingreso de datos'
    if pago_webpay.response_code == -2:
        estado = 'Error'
        mensaje = 'Error al procesar la transacción: parámetros tarjeta y/o cuenta asociada'
    if pago_webpay.response_code == -3:
        estado = 'Error'
        mensaje = 'Error interno de transbank al procesar la transacción'
    if pago_webpay.response_code == -4:
        estado = 'Error'
        mensaje = 'Transacción Rechazada por parte del emisor'
    if pago_webpay.response_code == -5:
        estado = 'Error'
        mensaje = 'Transacción rechazada con riesgo de posible fraude'

    return Response({
        'estado': estado,
        'mensaje': mensaje,
        'comprobante_pago': comprobante_pago,
    })


@api_view(['GET', ])
@permission_classes([IsAuthenticated])
def estado_pago_matricula(request, estudiante_id):
    """ API para consultar estado transacción webpay matricula desde el frontend """

    # Obtener estudiante
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except ObjectDoesNotExist:
        return Response(
            {'mensaje': 'El estudiante enviado no existe.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Obtener matricula estudiante
    try:
        matricula = MatriculaEstudiante.objects.get(
            estudiante=estudiante, proceso_matricula__activo=True)
    except MatriculaEstudiante.DoesNotExist:
        return Response(
            {'mensaje': 'no existe una matrícula asociada al estudiante enviado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Retorna: { estado, mensaje, comprobante }
    return estado_pago_webpay(
        orden_compra=matricula.orden_compra,
        producto='matrícula',
    )


@api_view(['GET', ])
@permission_classes([IsAuthenticated])
def estado_pago_arancel(request, estudiante_id):
    """ API para consultar estado transacción webpay arancel desde el frontend """

    # Obtener estudiante
    try:
        estudiante = Estudiante.objects.get(id=estudiante_id)
    except ObjectDoesNotExist:
        return Response(
            {'mensaje': 'El estudiante solicitado no existe.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Obtener arancel estudiante
    try:
        arancel = ArancelEstudiante.objects.get(
            estudiante=estudiante, proceso_matricula__activo=True)
    except ArancelEstudiante.DoesNotExist:
        return Response(
            {'mensaje': 'no existe un arancel asociado al estudiante enviado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Retorna: { estado, mensaje, comprobante }
    return estado_pago_webpay(
        orden_compra=arancel.orden_compra,
        producto='arancel',
    )


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
