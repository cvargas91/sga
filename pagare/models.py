from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone

from general.models import ModeloRegistraFechas


class ModalidadCuotaPagare(ModeloRegistraFechas):
    proceso_matricula = models.ForeignKey('matricula.ProcesoMatricula', on_delete=models.PROTECT)
    plan = models.ForeignKey('academica.Plan', on_delete=models.PROTECT)
    cantidad_cuotas = models.PositiveSmallIntegerField()

    cursos_asociados = [
        (0, 'primer año'),
        (1, 'cursos superiores'),
    ]
    curso_asociado = models.PositiveSmallIntegerField(
        choices=cursos_asociados,
        help_text='permite definir pagarés diferenciados para estudiantes nuevos y antiguos',
    )

    link_pagare = models.CharField(
        max_length=200, blank=True,
        help_text='''
ID del documento en google drive para generar el link de descarga del pagaré.<br>
Para obtenerlo se debe abrir el documento en una ventana nueva y en la url se encuentra el id.<br>
e.g: en <a>https://drive.google.com/file/d/1scpjrjnHdwgjc8Ya-oSQyYjLMyh4BgQv/view</a>
el id es <b>1scpjrjnHdwgjc8Ya-oSQyYjLMyh4BgQv</b>.
        ''',
    )
    fecha_primera_cuota = models.CharField(
        max_length=50, blank=True,
        help_text='utilizado solo para informar al estudiante',
    )

    descripcion = models.CharField(max_length=200, blank=True)
    interes_mensual_mora = models.FloatField(null=True, blank=True)
    decreto = models.CharField(max_length=50, blank=True)
    decreto_ano = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'modalidad_cuota_pagare'
        unique_together = ['proceso_matricula', 'plan', 'cantidad_cuotas', 'curso_asociado']

    def __str__(self):
        return (
            f'{self.proceso_matricula.ano} - {self.plan} - {self.cantidad_cuotas} cuotas '
            f'({self.get_curso_asociado_display()})'
        )


class Pagare(ModeloRegistraFechas):
    arancel_estudiante = models.ForeignKey(
        'matricula.ArancelEstudiante', on_delete=models.PROTECT, related_name='pagares')
    rut_estudiante = models.CharField(max_length=50)

    fecha = models.DateField(auto_now_add=True)

    modalidad_cuota = models.ForeignKey(
        'ModalidadCuotaPagare', on_delete=models.PROTECT, null=True, blank=True)
    numero_cuotas = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='pensado para permitir crear pagarés sin una modalidad de cuota definida',
    )

    monto_arancel = models.PositiveIntegerField()
    monto_total_extras = models.PositiveIntegerField(
        default=0,
        help_text='para poder agregar valores extras, como matrícula o deudas anteriores',
    )

    validado = models.BooleanField(default=False)
    validado_por = models.ForeignKey(
        'persona.Persona', on_delete=models.PROTECT, null=True, blank=True)
    validado_fecha = models.DateField(null=True, blank=True)

    documento_escaneado = models.FileField(upload_to='pagares/', null=True)

    estados = [
        (0, 'esperando recepción'),
        (1, 'recibido - pago pendiente'),
        (2, 'pago finalizado'),
        (3, 'anulado por gratuidad'),
        (4, 'anulado por cambio de carrera'),
        (5, 'anulado por repactación de deuda'),
        (6, 'anulado por retracto'),
        (7, 'anulado (otro motivo)'),
        (8, 'cancelado por cambio de forma de pago'),
    ]
    estado = models.PositiveSmallIntegerField(choices=estados, default=0)

    class Meta:
        db_table = 'pagare'

        permissions = [
            ("recibir_pagare", "Puede marcar pagarés como recibidos"),
        ]

    def cantidad_cuotas(self):
        if self.modalidad_cuota:
            return self.modalidad_cuota.cantidad_cuotas
        return self.numero_cuotas

    def __str__(self):
        return (
            f'{self.arancel_estudiante} - {self.cantidad_cuotas()} cuotas '
            f'({self.get_estado_display()})'
        )

    def recibir_pagare(self, request):
        try:
            persona = request.user.persona
        except ObjectDoesNotExist:
            persona = None

        self.estado = 1  # recibido
        self.validado = True
        self.validado_por = persona
        self.validado_fecha = timezone.now()
        self.save()
        return


class HistorialEstadoPagare(ModeloRegistraFechas):
    """ no utilizado """
    pagare = models.ForeignKey('Pagare', on_delete=models.PROTECT)
    estado_anterior = models.PositiveSmallIntegerField(choices=Pagare.estados)
    estado_actual = models.PositiveIntegerField(choices=Pagare.estados)
    autor_cambio = models.ForeignKey(
        'persona.Persona', on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = 'historial_estado_pagare'


class PagarePersona(ModeloRegistraFechas):
    """ Pensado para registrar a los avales y tutores del estudiante, no utilizado. """
    pagare = models.ForeignKey('Pagare', on_delete=models.PROTECT)
    tipos_personas = [
        (0, 'aval'),
        (1, 'tutor legal'),
    ]
    tipo_persona = models.PositiveSmallIntegerField(choices=tipos_personas)

    rut = models.CharField(max_length=50)
    nombres = models.CharField(max_length=50)
    primer_apellido = models.CharField(max_length=50)
    segundo_apellido = models.CharField(max_length=50)

    carnet = models.FileField(upload_to='pagares/aval/')

    direccion = models.CharField(max_length=50)
    comuna = models.ForeignKey('general.Comuna', on_delete=models.PROTECT)
    telefono = models.CharField(max_length=50)

    class Meta:
        db_table = 'pagare_persona'


class TipoExtraPagare(ModeloRegistraFechas):
    """ pensado para registrar los distintos tipos de cobros extras (matrícula, deuda, etc),
    no utilizado. """
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = 'tipo_extra_pagare'


class PagoExtraPagare(ModeloRegistraFechas):
    """ pensado para registrar el detalle de los cobros extras que pueda tener un pagaré,
    no utilizado. """
    pagare = models.ForeignKey('Pagare', on_delete=models.PROTECT)
    tipo_extra = models.ForeignKey('TipoExtraPagare', on_delete=models.PROTECT)
    monto = models.PositiveIntegerField()
    justificacion = models.CharField(max_length=200)

    class Meta:
        db_table = 'pago_extra_pagare'


class FechaCuotaPagare(ModeloRegistraFechas):
    """ Define en qué fechas se debe pagar cada cuota de una modalidad e cuota, no utilizado. """
    modalidad_cuota = models.ForeignKey('ModalidadCuotaPagare', on_delete=models.PROTECT)
    numero_cuota = models.PositiveSmallIntegerField()
    fecha_pago = models.DateField()

    class Meta:
        db_table = 'fecha_cuota_pagare'


class CuotaPagare(ModeloRegistraFechas):
    """ Define cuánto y cuándo se debe pagar cada cuota, no utilizado. """
    pagare = models.ForeignKey('Pagare', on_delete=models.PROTECT)
    numero_cuota = models.PositiveSmallIntegerField()
    monto_a_pagar = models.PositiveIntegerField()

    fecha_cuota_pagare = models.ForeignKey(
        'FechaCuotaPagare', on_delete=models.PROTECT, null=True, blank=True)
    # en caso de no usar una modalidad definida
    fecha_cuota = models.DateField(
        null=True, blank=True,
        help_text='para poder agregar cuotas manualmente, sin una modalidad cuota definida',
    )

    monto_pagado = models.PositiveIntegerField()
    fecha_pago = models.DateField()
    orden_compra = models.IntegerField()

    estados = [
        (0, 'pendiente'),
        (1, 'expirada'),
        (2, 'pagada'),
        (3, 'anulada'),
    ]
    estado = models.PositiveSmallIntegerField(choices=estados)

    class Meta:
        db_table = 'cuota_pagare'
