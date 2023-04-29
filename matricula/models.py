from django.db import models
from django.db.models import Max
from django.utils import timezone

from general.models import ModeloRegistraFechas

from mails.funciones import enviar_confirmacion_matricula
from persona.google import crear_mail_institucional
from certificados.generador import crear_certificado_matricula
# from inscripcion.algoritmos import inscribir_asignaturas_primer_semestre


class ProcesoMatriculaManager(models.Manager):
    def get_by_natural_key(self, ano):
        return self.get(ano=ano)


class ProcesoMatricula(ModeloRegistraFechas):
    ano = models.PositiveSmallIntegerField(unique=True)
    fecha_vigencia = models.DateField(
        help_text='''fecha hasta la cuál es válida una matrícula de este proceso, para validar
        que solo estudiantes matriculados puedan realizar inscripción académica y otras acciones
        similares que puedan ocurrir el año siguiente de la matrícula'''
    )
    periodo_ingreso = models.ForeignKey(
        'curso.Periodo', on_delete=models.PROTECT,
        help_text='periodo de ingreso para los estudiantes nuevos de este proceso de matrícula'
    )
    activo = models.BooleanField(
        help_text='define qué proceso está en progreso, independiente del periodo activo'
    )

    class Meta:
        db_table = 'proceso_matricula'

    def __str__(self):
        return f'proceso matrícula {self.ano} {"(activo)" if self.activo else ""}'

    objects = ProcesoMatriculaManager()

    def natural_key(self):
        return (self.ano, )

    def save(self, *args, **kwargs):
        # desactivar todos los otros procesos cuando se activa un proceso nuevo
        if self.activo:
            ProcesoMatricula.objects.update(activo=False)

        super().save(*args, **kwargs)


class ViaIngreso(ModeloRegistraFechas):
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = 'via_ingreso'

    def __str__(self):
        return f'{self.nombre}'


class PeriodoProcesoMatricula(ModeloRegistraFechas):
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    publicos = [
        (0, 'primer año'),
        (1, 'curso superior'),
        (2, 'educación continua'),
    ]
    publico = models.PositiveSmallIntegerField(choices=publicos)
    planes = models.ManyToManyField(
        'academica.Plan', blank=True,
        help_text='''si no se deja en blanco, solo los planes asociados se pueden matricular
                    en este periodo''')

    descripcion = models.CharField(max_length=200)

    dcto_oportuno = models.PositiveSmallIntegerField(default=0)
    fecha_entrega_pagare = models.DateField(null=True, blank=True)
    fecha_pago_matricula = models.DateField(null=True, blank=True)
    fecha_pago_arancel = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'periodo_proceso_matricula'

    def __str__(self):
        return f'{self.proceso_matricula} {self.fecha_inicio}-{self.fecha_fin}'

    @staticmethod
    def hay_periodo_abierto(publico: int, plan=None):
        return PeriodoProcesoMatricula.periodos_abiertos(publico, plan).exists()

    @staticmethod
    def periodos_abiertos(publico: int, plan=None):
        fecha_ahora = timezone.now()

        periodos = PeriodoProcesoMatricula.objects.filter(
            proceso_matricula=ProcesoMatricula.objects.get(activo=True),
            fecha_inicio__lte=fecha_ahora,
            fecha_fin__gte=fecha_ahora,
            publico=publico,
        )

        if plan is not None:
            return periodos.filter(planes=plan)

        return periodos


class PostulanteDefinitivo(ModeloRegistraFechas):
    persona = models.ForeignKey('persona.Persona', on_delete=models.PROTECT)
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    plan = models.ForeignKey('academica.plan', on_delete=models.PROTECT)
    via_ingreso = models.ForeignKey('ViaIngreso', on_delete=models.PROTECT)
    PACE = models.BooleanField(
        default=False,
        help_text='''define si es que el estudiante proviene de un programa PACE,
                    independiente de su vía de ingreso'''
    )

    numero_demre = models.CharField(
        max_length=50,
        help_text='''Este número se utiliza como la contraseña del estudiante para
                    ingresar al portal de matrícula'''
    )

    resultados_postulacion = [
        (0, 'seleccionado'),
        (1, 'lista de espera'),
    ]
    resultado_postulacion = models.PositiveSmallIntegerField(choices=resultados_postulacion)
    posicion_lista = models.PositiveSmallIntegerField()

    preseleccionado_gratuidad = models.BooleanField(
        default=False,
        help_text='''Atención: marcar esta opción resultará en un costo de matrícula y
                    arancel de $0 para el estudiante'''
    )

    habilitado = models.BooleanField()
    acepta_vacante = models.BooleanField(default=False)
    estudiante = models.OneToOneField(
        'persona.Estudiante', related_name='postulante',
        on_delete=models.PROTECT, null=True, blank=True
    )

    # puntajes de ingreso
    promedio_NEM = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    puntaje_NEM = models.DecimalField(max_digits=4, decimal_places=0, null=True, blank=True)
    puntaje_ranking = models.DecimalField(max_digits=4, decimal_places=0, null=True, blank=True)

    puntaje_matematica = models.DecimalField(max_digits=3, decimal_places=0, null=True, blank=True)
    puntaje_matematica_m1 = models.DecimalField(max_digits=4, decimal_places=0, null=True,
                                                blank=True)
    puntaje_matematica_m2 = models.DecimalField(max_digits=4, decimal_places=0, null=True,
                                                blank=True)
    puntaje_lenguaje = models.DecimalField(max_digits=4, decimal_places=0, null=True, blank=True)
    promedio_lenguaje_matematica = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True)
    percentil_lenguaje_matematica = models.DecimalField(
        max_digits=2, decimal_places=0, null=True, blank=True)

    percentil_50 = models.CharField(max_length=1, null=True, blank=True)
    percentil_60 = models.CharField(max_length=1, null=True, blank=True)

    puntaje_historia = models.DecimalField(max_digits=4, decimal_places=0, null=True, blank=True)
    puntaje_ciencias = models.DecimalField(max_digits=4, decimal_places=0, null=True, blank=True)
    modulo_ciencias = models.CharField(max_length=20, blank=True)

    puntaje_ponderado = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'postulante_definitivo'
        unique_together = ('persona', 'proceso_matricula', 'plan', 'via_ingreso')

    def __str__(self):
        return f'{self.persona} {self.proceso_matricula} {self.plan} (ingreso {self.via_ingreso})'

    def etapa_actual(self):
        if self.acepta_vacante:
            etapas = EtapaEstudiante.objects.filter(
                estudiante=self.estudiante,
                proceso_matricula=ProcesoMatricula.objects.get(activo=True)
            )
            ultima_etapa = etapas.aggregate(ultima=Max('etapa_matricula__numero'))['ultima']
            return ultima_etapa

        return 0

    def completo_proceso(self):
        # chequear que llegó a última etapa
        etapa_actual = self.etapa_actual()
        if etapa_actual < 4:
            return False

        # chequear que pagó matrícula
        if self.estudiante:
            matricula = MatriculaEstudiante.objects.get(
                proceso_matricula=self.proceso_matricula,
                estudiante=self.estudiante
            )
            return matricula.estado == 1

        return False


class RegistroPostulanteHabilitado(ModeloRegistraFechas):
    """ no utilizado """
    postulante_definitivo = models.ForeignKey('PostulanteDefinitivo', on_delete=models.PROTECT)
    estado_anterior = models.BooleanField()
    autor_cambio = models.ForeignKey('persona.Persona', on_delete=models.PROTECT)
    fecha_cambio = models.DateField()

    class Meta:
        db_table = 'registro_postulante_habilitado'


class EtapaMatricula(ModeloRegistraFechas):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=200)
    numero = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        db_table = 'etapa_matricula'

    def __str__(self):
        return self.nombre


class EtapaEstudiante(ModeloRegistraFechas):
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=models.PROTECT)
    etapa_matricula = models.ForeignKey('EtapaMatricula', on_delete=models.PROTECT)
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)

    fecha = models.DateField(auto_now_add=True)
    descripcion = models.CharField(max_length=200)

    class Meta:
        db_table = 'etapa_estudiante'
        unique_together = ['estudiante', 'etapa_matricula', 'proceso_matricula']

    def __str__(self):
        return f'{self.estudiante} - {self.etapa_matricula} - {self.creado.strftime("%d/%m %H:%M")}'


class ValorMatricula(ModeloRegistraFechas):
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    plan = models.ForeignKey('academica.Plan', on_delete=models.PROTECT)
    valor = models.PositiveIntegerField()

    decreto = models.CharField(max_length=200)
    decreto_ano = models.PositiveSmallIntegerField()

    producto = models.ForeignKey('pagos.Productos', on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = 'valor_matricula'
        unique_together = ['proceso_matricula', 'plan']

    def __str__(self):
        return f'{self.proceso_matricula} - {self.plan} - {self.valor}'


class ValorArancel(ModeloRegistraFechas):
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    plan = models.ForeignKey('academica.Plan', on_delete=models.PROTECT)
    valor = models.PositiveIntegerField()

    decreto = models.CharField(max_length=200)
    decreto_ano = models.PositiveSmallIntegerField()

    producto = models.ForeignKey('pagos.Productos', on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = 'valor_arancel'
        unique_together = ['proceso_matricula', 'plan']

    def __str__(self):
        return f'{self.proceso_matricula} - {self.plan}: {self.valor}'


class OfertaAcademica(ModeloRegistraFechas):
    """ no utilizado """
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    plan = models.ForeignKey('academica.Plan', on_delete=models.PROTECT)

    cupos_regulares = models.PositiveSmallIntegerField()
    cupos_BEA = models.PositiveSmallIntegerField()
    cupos_PACE = models.PositiveSmallIntegerField()
    cupos_especiales = models.PositiveSmallIntegerField()

    class Meta:
        db_table = 'oferta_academica'
        unique_together = ['proceso_matricula', 'plan']

    def __str__(self):
        return f'{self.proceso_matricula} - {self.plan}'


class GratuidadEstudiante(ModeloRegistraFechas):
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=models.PROTECT)
    tiene_gratuidad = models.BooleanField(default=False)

    class Meta:
        db_table = 'gratuidad_estudiante'
        unique_together = ['proceso_matricula', 'estudiante']

    def __str__(self):
        return f'{self.proceso_matricula} {self.estudiante}'


class ArancelEstudiante(ModeloRegistraFechas):
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    periodo_matricula = models.ForeignKey(
        'PeriodoProcesoMatricula', on_delete=models.PROTECT, null=True, blank=True,
        help_text='se debe guardar el periodo para conocer las fechas límites asociadas',
    )
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=models.PROTECT)
    valor_arancel = models.ForeignKey('ValorArancel', on_delete=models.PROTECT)

    monto = models.IntegerField(
        help_text='corresponde al monto final que debe pagar el estudiante, considerando beneficios'
    )

    tiene_beneficios = models.BooleanField(default=False)
    beneficios_monto_total = models.IntegerField(default=0)
    descripcion_beneficios = models.TextField(blank=True)

    pago_cuotas = models.BooleanField(
        default=False,
        help_text='define si este arancel se está pagando con pagaré (true) o al contado (false)'
    )

    orden_compra = models.ForeignKey(
        'pagos.OrdenCompra', on_delete=models.PROTECT, null=True, blank=True)

    pagare = models.ForeignKey(
        'pagare.Pagare', on_delete=models.PROTECT, null=True, blank=True, related_name='arancel')

    class Meta:
        db_table = 'arancel_estudiante'
        unique_together = ['proceso_matricula', 'estudiante']

    def __str__(self):
        return f'{self.proceso_matricula} {self.estudiante} {self.monto}'

    # def validar(self):
    #     # marcar estudiante como regular si su estado era matrícula pendiente
    #     if self.estudiante.estado_estudiante_id == 6:
    #         self.estudiante.estado_estudiante_id = 4
    #         self.estudiante.save()

    #     contrasena = None
    #     certificado = None

    #     # crear mails institucionales para estudiantes nuevos
    #     if self.estudiante.es_estudiante_nuevo():
    #         contrasena = crear_mail_institucional(self.estudiante)

    #         #  crear certificado de matrícula para primer año pregrado
    #         if self.estudiante.es_estudiante_pregrado():
    #             certificado = crear_certificado_matricula(self.estudiante)

    #     # enviar mail de confirmación
    #     enviar_confirmacion_matricula(
    #         estudiante=self.estudiante,
    #         contrasena=contrasena,
    #         certificado=certificado
    #     )
    #     return


class InhabilitantesMatricula(ModeloRegistraFechas):
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=models.PROTECT)

    tiene_deuda_finanzas = models.BooleanField(default=False)
    comentario_finanzas = models.CharField(max_length=1000, blank=True)

    tiene_deuda_biblioteca = models.BooleanField(default=False)
    comentario_biblioteca = models.CharField(max_length=1000, blank=True)

    class Meta:
        db_table = 'inhabilitantes_matricula'
        unique_together = ['proceso_matricula', 'estudiante']

    def __str__(self):
        return f'{self.proceso_matricula} {self.estudiante}'


class MatriculaEstudiante(ModeloRegistraFechas):
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    periodo_matricula = models.ForeignKey(
        'PeriodoProcesoMatricula', on_delete=models.PROTECT, null=True, blank=True,
        help_text='se debe guardar el periodo para conocer las fechas límites asociadas',
    )
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=models.PROTECT)

    monto_final = models.IntegerField(
        help_text='corresponde al monto final que debe pagar el estudiante, considerando beneficios'
    )

    tiene_beneficios = models.BooleanField(default=False)
    beneficios_monto_total = models.IntegerField(default=0)
    descripcion_beneficios = models.TextField(blank=True)

    estados = [
        (0, 'pendiente'),
        (1, 'válida'),
        (2, 'anulada por cambio de carrera'),
        (3, 'anulada por retracto'),
        (4, 'anulada por otro motivo'),
    ]
    estado = models.PositiveSmallIntegerField(choices=estados, default=0)

    orden_compra = models.ForeignKey(
        'pagos.OrdenCompra', on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = 'matricula_estudiante'
        unique_together = ['proceso_matricula', 'estudiante']

    def __str__(self):
        return f'{self.proceso_matricula} {self.estudiante}'

    def validar(self):
        # marcar estudiante como regular si su estado era matrícula pendiente
        if self.estudiante.estado_estudiante_id == 6:
            self.estudiante.estado_estudiante_id = 4
            self.estudiante.save()

        self.estado = 1  # valida
        self.save()

        contrasena = None
        certificado = None

        # crear mails institucionales para estudiantes nuevos
        if self.estudiante.es_estudiante_nuevo():
            contrasena = crear_mail_institucional(self.estudiante)

            #  crear certificado de matrícula para primer año pregrado
            if self.estudiante.es_estudiante_pregrado():
                certificado = crear_certificado_matricula(self.estudiante)
                # inscribir_asignaturas_primer_semestre(self.estudiante)

        # enviar mail de confirmación
        enviar_confirmacion_matricula(
            estudiante=self.estudiante,
            contrasena=contrasena,
            certificado=certificado
        )
        return


class TNEEstudiante(ModeloRegistraFechas):
    """ solo se utilizó en matrícula 2021 """
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=models.PROTECT)
    paga_TNE = models.BooleanField(default=False)

    orden_compra = models.ForeignKey(
        'pagos.OrdenCompra', on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        db_table = 'tne_estudiante'
        unique_together = ['proceso_matricula', 'estudiante']

    def __str__(self):
        return f'{self.proceso_matricula} {self.estudiante}'


class EstudianteRespondeEncuesta(ModeloRegistraFechas):
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=models.PROTECT)
    responde_encuesta = models.BooleanField(default=False)

    class Meta:
        db_table = 'estudiante_responde_encuesta'
        unique_together = ['proceso_matricula', 'estudiante']

    def __str__(self):
        return f'{self.proceso_matricula} {self.estudiante} ({self.responde_encuesta})'


class PostulanteEducacionContinua(ModeloRegistraFechas):
    persona = models.ForeignKey('persona.Persona', on_delete=models.PROTECT)
    proceso_matricula = models.ForeignKey('ProcesoMatricula', on_delete=models.PROTECT)
    plan = models.ForeignKey('academica.plan', on_delete=models.PROTECT)

    clave = models.CharField(max_length=50)

    resultados_postulacion = [
        (0, 'seleccionado'),
        (1, 'lista de espera'),
    ]
    resultado_postulacion = models.PositiveSmallIntegerField(choices=resultados_postulacion)
    posicion_lista = models.PositiveSmallIntegerField()
    habilitado = models.BooleanField(default=False)

    acepta_vacante = models.BooleanField(default=False)
    estudiante = models.OneToOneField(
        'persona.Estudiante', related_name='postulanteeducontinua',
        on_delete=models.PROTECT, null=True, blank=True)

    tipos_descuentos = [
        (0, 'monto fijo'),
        (1, 'porcentual'),
    ]
    tipo_descuento_arancel = models.PositiveSmallIntegerField(
        choices=tipos_descuentos, null=True, blank=True)
    monto_descuento_arancel = models.PositiveIntegerField(null=True, blank=True)
    descripcion_descuento_arancel = models.TextField(blank=True)

    tipo_descuento_matricula = models.PositiveSmallIntegerField(
        choices=tipos_descuentos, null=True, blank=True)
    monto_descuento_matricula = models.PositiveIntegerField(null=True, blank=True)
    descripcion_descuento_matricula = models.TextField(blank=True)

    class Meta:
        db_table = 'postulante_educacion_continua'
        unique_together = ('persona', 'proceso_matricula', 'plan')

    def __str__(self):
        return f'{self.persona} {self.proceso_matricula} {self.plan}'

    def etapa_actual(self):
        if self.estudiante:
            return self.estudiante.etapa_estudiante()

        return 0
