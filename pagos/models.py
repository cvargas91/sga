from django.db import models
from django.utils import timezone
from general.models import ModeloRegistraFechas


class CategoriasProductos(ModeloRegistraFechas):
    """ utilizado para marcar a qué proceso de matrícula corresponde (2021, 2022, etc). """
    nombre = models.CharField(max_length=100, null=False)
    estado = models.BooleanField(null=False, help_text='no utilizado en matrícula')

    class Meta:
        db_table = 'categorias_productos'

    def __str__(self):
        return f'{self.nombre}'


class SubCategoriasProductos(ModeloRegistraFechas):
    """ define el tipo de producto: matrícula, arancel o tne (solo utilizada en 2021). """
    nombre = models.CharField(max_length=100, null=False)
    estado = models.BooleanField(null=False, help_text='no utilizado en matrícula')

    class Meta:
        db_table = 'subcategorias_productos'

    def __str__(self):
        return f'{self.nombre}'


class Productos(ModeloRegistraFechas):
    categoria = models.ForeignKey('CategoriasProductos', on_delete=models.PROTECT, null=False)
    subcategoria = models.ForeignKey('SubCategoriasProductos', on_delete=models.PROTECT, null=False)
    nombre = models.CharField(max_length=200, null=False)

    codigo_interno = models.IntegerField(
        null=True, help_text='no utilizado en matrícula')
    observaciones_codigo_interno = models.CharField(
        max_length=200, null=True, help_text='no utilizado en matrícula')
    descripcion_corta = models.CharField(
        max_length=200, null=False, help_text='no utilizado en matrícula')
    descripcion_larga = models.CharField(
        max_length=400, null=False, help_text='no utilizado en matrícula')
    unidad_medida = models.CharField(
        max_length=40, null=True, help_text='no utilizado en matrícula')
    stock = models.IntegerField(
        null=False, help_text='no utilizado en matrícula')

    valor = models.IntegerField(null=False)

    valor_antes = models.IntegerField(
        null=True, help_text='no utilizado en matrícula')
    marca = models.CharField(
        max_length=200, null=True, help_text='no utilizado en matrícula')
    numero_serie = models.CharField(
        max_length=200, null=True, help_text='no utilizado en matrícula')
    destacado = models.BooleanField(
        null=True, help_text='no utilizado en matrícula')
    numero_vistas = models.IntegerField(
        null=True, help_text='no utilizado en matrícula')
    estado = models.BooleanField(
        null=False, help_text='no utilizado en matrícula')

    class Meta:
        db_table = 'productos'

    def __str__(self):
        return f'{self.nombre} ${self.valor}'


class ModalidadPago(ModeloRegistraFechas):
    """ presencial/remoto """
    nombre = models.CharField(max_length=50)
    estado = models.BooleanField(null=False, help_text='no utilizado en matrícula')

    class Meta:
        db_table = 'modalidad_pago'

    def __str__(self):
        return f'{self.nombre}'


class FormaPago(ModeloRegistraFechas):
    """ caja/efectivo/debito/credito/transferencia/deposito/webpay """
    modalidad_pago = models.ForeignKey('ModalidadPago', on_delete=models.PROTECT)
    nombre = models.CharField(max_length=50)
    estado = models.BooleanField(null=False, help_text='no utilizado en matrícula')

    class Meta:
        db_table = 'forma_pago'

    def __str__(self):
        return f'{self.nombre}'


class OrdenCompra(ModeloRegistraFechas):
    persona = models.ForeignKey('persona.Persona', on_delete=models.PROTECT)
    forma_pago = models.ForeignKey('FormaPago', on_delete=models.PROTECT)
    folio_dte = models.CharField(max_length=200, null=True, blank=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)

    monto_total = models.IntegerField(default=0, help_text='monto inicial sin contar beneficios')
    total_descuento_beneficios = models.IntegerField(default=0)

    ip = models.CharField(max_length=200, null=True, blank=True)
    id_sesion = models.CharField(max_length=200, null=True, blank=True)

    token_webpay = models.CharField(
        max_length=200, null=True, blank=True,
        help_text='utilizado para integración con webpay',
    )
    pago_app = models.CharField(
        max_length=200, null=True, blank=True, help_text='no utilizado en matrícula')
    comentario = models.CharField(max_length=200, null=True, blank=True)

    estado = models.BooleanField(
        null=False,
        help_text='define si la orden compra terminó o no, independiente del resultado',
    )
    estados_pago = [
        (0, 'pendiente'),   # 0 - Pendiente de pago (Cuando es creada)
        (1, 'pagada'),      # 1 - Pagada/Cerrada (en todas sus formas de pago)
        (2, 'rechazada'),   # 2 - Rechazada (diversos casos: caída internet, cierre navegador, etc)
        (3, 'anulada'),     # 3 - Anulada por retracto webpay (REFUND: hasta 1 hr posterior al pago)
        (4, 'inválida'),   # 4 - Cancelada por cambio en forma de pago
    ]
    estado_pago = models.PositiveSmallIntegerField(choices=estados_pago)

    class Meta:
        db_table = 'orden_compra'

        permissions = [
            ("recibir_pagos", "Puede marcar ordenes de compra como pagadas"),
        ]

    def __str__(self):
        return (
            f'{self.id} {self.persona} {self.forma_pago} '
            f'${self.monto_a_pagar()} '
            f'({self.get_estado_pago_display()})'
        )

    def monto_a_pagar(self):
        return self.monto_total - self.total_descuento_beneficios

    def validar(self):
        self.estado_pago = 1
        self.fecha_pago = timezone.now()
        self.estado = True
        self.save()
        return

    def rechazar(self):
        self.estado_pago = 2
        self.fecha_pago = timezone.now()
        self.estado = True
        self.save()
        return


class OrdenCompraDetalle(ModeloRegistraFechas):
    """ guarda los productos que se compraron en una orden de compra """
    orden_compra = models.ForeignKey('OrdenCompra', on_delete=models.CASCADE, null=False)
    producto = models.ForeignKey('Productos', on_delete=models.PROTECT, null=False)
    valor = models.IntegerField(null=False)
    cantidad = models.IntegerField(null=False)
    descuento = models.IntegerField(null=True, help_text='no utilizado en matrícula')

    class Meta:
        db_table = 'orden_compra_detalle'

    def __str__(self):
        return f'{self.orden_compra} - {self.producto}'


class PagoWebPay(ModeloRegistraFechas):
    """
    registra detalle de transacciones realizadas por webpay, para más detalle consultar
    la documentación en https://transbankdevelopers.cl/referencia/webpay#ambientes-y-credenciales
    """
    orden_compra = models.ForeignKey('OrdenCompra', on_delete=models.CASCADE, null=False)
    token = models.CharField(
        max_length=200, null=False, help_text='generado por webpay para realizar integración')
    url_redirection = models.CharField(max_length=200, null=True)
    buy_order = models.CharField(
        max_length=200, null=True, help_text='se utiliza el id de la orden de compra')
    session_id = models.CharField(
        max_length=200, null=True, help_text='no se utilizan sesiones en SGA')
    amount = models.IntegerField(default=0, null=False)

    # campos para registrar resultado
    vci = models.CharField(
        max_length=200, null=True, help_text='resultado de autenticación')
    status = models.CharField(
        max_length=200, null=True, help_text='estado de la transacción')
    card_number = models.CharField(
        max_length=200, null=True, help_text='útlimos 4 dígitos')
    accounting_date = models.CharField(
        max_length=200, null=True, help_text='fecha autorización (MMDD)')
    transaction_date = models.CharField(
        max_length=200, null=True, help_text='fecha-hora autorización (yyyy-mm-ddTHH: mm: ss.xxxZ)')
    authorization_code = models.CharField(
        max_length=200, null=True, help_text='código de autorización')
    payment_type_code = models.CharField(
        max_length=200, null=True, help_text='tipo de venta, explicados en función completar')
    response_code = models.IntegerField(
        null=True, help_text='0 si es aprobada, negativo en caso contrario')
    installments_amount = models.IntegerField(
        null=True, help_text='valor de cuotas')
    installments_number = models.IntegerField(
        null=True, help_text='número de cuotas')
    balance = models.IntegerField(
        null=True, help_text='no utilizado en matrícula')

    class Meta:
        db_table = 'pago_webpay'

    def __str__(self):
        return f'{self.orden_compra}'

    def completar(self, response):
        self.vci = response.vci
        self.status = response.status
        self.card_number = response.card_detail.card_number
        self.accounting_date = response.accounting_date
        self.transaction_date = response.transaction_date
        self.authorization_code = response.authorization_code
        self.payment_type_code = response.payment_type_code
        self.response_code = response.response_code

        """
        VD = Venta Débito.
        VN = Venta Normal.
        VC = Venta en cuotas.
        SI = 3 cuotas sin interés.
        S2 = 2 cuotas sin interés.
        NC = N Cuotas sin interés
        VP = Venta Prepago.
        """
        if response.response_code == 'VC':
            self.installments_number = response.installments_number
            self.installments_amount = response.installments_amount

        if response.response_code == 'SI':
            self.installments_number = 3
            self.installments_amount = response.installments_amount

        if response.response_code == 'S2':
            self.installments_number = 2
            self.installments_amount = response.installments_amount

        if response.response_code == 'NC':
            self.installments_number = 0
            self.installments_amount = response.installments_amount

        if response.response_code == 'VD' or response.response_code == 'VN' \
                or response.response_code == 'VP':
            self.installments_number = 0
            self.installments_amount = 0

        self.save()
        return

    def rechazar(self, buy_order):
        self.response_code = -4
        self.save()

        orden_compra = OrdenCompra.objects.get(id=buy_order, token_webpay=self.token)
        orden_compra.rechazar()
        orden_compra.save()
        return


class PagoTransferenciaBancaria(ModeloRegistraFechas):
    """ no utilizado """
    orden_compra = models.ForeignKey('OrdenCompra', on_delete=models.CASCADE, null=False)
    nombre_titular_cuenta = models.CharField(max_length=200, null=False)
    rut_titular_cuenta = models.CharField(max_length=20, null=False)
    email_titular_cuenta = models.EmailField(max_length=200, null=False)
    numero_operacion = models.CharField(max_length=50, null=False)
    fecha_pago = models.DateTimeField(null=False)
    valor = models.IntegerField(null=False)
    mensaje = models.CharField(max_length=200, null=True)
    estado = models.BooleanField(null=False)

    class Meta:
        db_table = 'pago_transferencia_bancaria'

    def __str__(self):
        return f'{self.estado}'


class PagoDepositoBancario(ModeloRegistraFechas):
    """ no utilizado """
    orden_compra = models.ForeignKey('OrdenCompra', on_delete=models.CASCADE, null=False)
    nombre_titular_cuenta = models.CharField(max_length=200, null=False)
    rut_titular_cuenta = models.CharField(max_length=20, null=False)
    numero_operacion = models.CharField(max_length=50, null=False)
    fecha_pago = models.DateTimeField(null=False)
    valor = models.IntegerField(null=False)
    estado = models.BooleanField(null=False)

    class Meta:
        db_table = 'pago_deposito_bancario'

    def __str__(self):
        return f'{self.estado}'


class PagoRedCompra(ModeloRegistraFechas):
    """ no utilizado """
    orden_compra = models.ForeignKey('OrdenCompra', on_delete=models.CASCADE, null=False)
    credito_cuotas = models.IntegerField(null=True)
    credito_sin_cuotas = models.IntegerField(null=True)
    debito = models.IntegerField(null=True)
    prepago = models.IntegerField(null=True)
    valor = models.IntegerField(null=False)
    numero_operacion = models.IntegerField(null=False)
    fecha_pago = models.DateTimeField(null=False)
    lectura_banda = models.IntegerField(null=True)
    chip = models.IntegerField(null=True)
    estado = models.BooleanField(null=False)

    class Meta:
        db_table = 'pago_red_compra'

    def __str__(self):
        return f'{self.estado}'


class Bancos(ModeloRegistraFechas):
    """ no utilizado """
    nombre = models.CharField(max_length=200, null=False)
    estado = models.BooleanField(null=False)

    class Meta:
        db_table = 'bancos'

    def __str__(self):
        return f'{self.nombre}'


class PagoCheque(ModeloRegistraFechas):
    """ no utilizado """
    orden_compra = models.ForeignKey('OrdenCompra', on_delete=models.CASCADE, null=False)
    banco = models.ForeignKey('Bancos', on_delete=models.PROTECT, null=False)
    numero_cheque = models.IntegerField(null=False)
    valor = models.IntegerField(null=False)
    fecha_pago = models.DateTimeField(null=False)
    nom_orden_de = models.IntegerField(null=True)
    nom_no_orden_de = models.IntegerField(null=True)
    estado = models.BooleanField(null=False)
    tipos_cheque = [
        (0, 'al_portador'),
        (1, 'nominativo'),
        (2, 'cruzado'),
        (3, 'conformado'),
        (4, 'viajero'),
    ]
    tipo_cheque = models.PositiveSmallIntegerField(choices=tipos_cheque)

    class Meta:
        db_table = 'pago_cheque'

    def __str__(self):
        return f'{self.estado}'


class PagoEfectivo(ModeloRegistraFechas):
    """ no utilizado """
    orden_compra = models.ForeignKey('OrdenCompra', on_delete=models.CASCADE, null=False)
    monto_pagado = models.IntegerField(null=False)
    monto_vuelto = models.IntegerField(null=False)
    monto_total = models.IntegerField(null=False)
    estado = models.BooleanField(null=False)

    class Meta:
        db_table = 'pago_efectivo'

    def __str__(self):
        return f'{self.estado}'


class DTE(ModeloRegistraFechas):
    """ no utilizado """
    folio = models.IntegerField(null=False)
    codigo_tipo_dte_api = models.IntegerField(null=False)
    ind_servicio = models.IntegerField(null=True)
    fecha_emision = models.DateTimeField(null=False)
    rut_emisor = models.CharField(max_length=50, null=False)
    rut_receptor = models.CharField(max_length=50, null=False)
    nombre_razon_social = models.CharField(max_length=200, null=False)
    giro = models.CharField(max_length=200, null=False)
    direccion = models.CharField(max_length=200, null=False)
    comuna = models.ForeignKey('general.Comuna', on_delete=models.PROTECT, null=False)
    ciudad = models.CharField(max_length=100, null=True)
    path_file_pdf = models.CharField(max_length=200, null=True)
    estado = models.BooleanField(null=False)
    tipos_dte = [
        (0, 'boleta_iva'),
        (1, 'boleta_exenta'),
        (2, 'factura_iva'),
        (3, 'factura_exenta'),
        (4, 'nota_credito'),
    ]
    tipo_dte = models.PositiveSmallIntegerField(choices=tipos_dte)

    class Meta:
        db_table = 'dte'

    def __str__(self):
        return f'{self.estado}'
