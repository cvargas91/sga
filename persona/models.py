import os
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Max
from django.db.models.signals import post_save
from rest_framework.serializers import ValidationError

from general.models import ModeloRegistraFechas
from matricula.models import ProcesoMatricula, EtapaEstudiante, EtapaMatricula
from curso.models import Periodo


def get_persona_or_validation_error(self):
    try:
        return self.persona
    except self._meta.model.persona.RelatedObjectDoesNotExist:
        raise ValidationError({'detail': 'El usuario no tiene una persona asociada'})


User.add_to_class('get_persona', get_persona_or_validation_error)


def dir_contratos():
    return os.path.join(settings.MEDIA_ROOT, 'contratos')


class Persona(ModeloRegistraFechas):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='persona')

    tipos_identificacion = [
        (0, 'cedula de identidad'),
        (1, 'pasaporte'),
    ]
    tipo_identificacion = models.PositiveSmallIntegerField(choices=tipos_identificacion, default=0)
    numero_documento = models.CharField(unique=True, max_length=50)
    digito_verificador = models.CharField(
        max_length=1, null=True, blank=True, help_text='solo se usa para cedula de identidad')

    nombres = models.CharField(max_length=100)
    apellido1 = models.CharField(max_length=100, blank=True)
    apellido2 = models.CharField(max_length=100, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexos = [
        (0, 'mujer'),
        (1, 'hombre'),
        (2, 'no especifica'),
    ]
    sexo = models.PositiveSmallIntegerField(choices=sexos, default=2)
    mail_institucional = models.EmailField(
        max_length=200, null=True, blank=True, unique=True,
        help_text='usado para login con google auth',
    )

    genero = models.CharField(max_length=50, blank=True)
    nombre_social = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to='fotos_perfil', max_length=200, null=True, blank=True)

    biografia = models.CharField(max_length=300, blank=True)
    mail_secundario = models.EmailField(max_length=200, blank=True)
    telefono_fijo = models.CharField(max_length=20, blank=True)
    telefono_celular = models.CharField(max_length=20, blank=True)

    nacionalidad = models.ForeignKey(
        'general.Pais', on_delete=models.PROTECT, null=True, blank=True)
    ciudad_origen = models.CharField(max_length=200, blank=True)

    # dirección en formato DEMRE
    direccion_calle = models.CharField(max_length=200, blank=True)
    direccion_numero = models.CharField(max_length=50, blank=True)
    direccion_block = models.CharField(max_length=50, blank=True)
    direccion_depto = models.CharField(max_length=50, blank=True)
    direccion_villa = models.CharField(max_length=200, blank=True)
    direccion_comuna = models.ForeignKey(
        'general.Comuna', on_delete=models.PROTECT, null=True, blank=True)

    direccion_coyhaique = models.CharField(max_length=200, blank=True)

    # contacto de emergencia
    emergencia_nombre = models.CharField(max_length=100, blank=True)
    emergencia_parentezco = models.CharField(max_length=100, blank=True)
    emergencia_telefono_fijo = models.CharField(max_length=100, blank=True)
    emergencia_telefono_laboral = models.CharField(max_length=100, blank=True)
    emergencia_telefono_celular = models.CharField(max_length=100, blank=True)
    emergencia_mail = models.CharField(max_length=100, blank=True)

    # información de educación continua
    educontinua_cargo = models.CharField(max_length=100, blank=True)
    educontinua_empresa = models.CharField(max_length=100, blank=True)
    educontinua_mail_laboral = models.CharField(max_length=100, blank=True)

    autoriza_uso_imagen = models.BooleanField(default=False)
    acepta_contrato = models.BooleanField(default=False)
    archivo_contrato = models.FilePathField(path=dir_contratos, null=True, blank=True)

    class Meta:
        db_table = 'persona'

    def nombre(self):
        if self.nombre_social:
            return self.nombre_social
        return self.nombres

    def nombre_legal(self):
        return f'{self.apellido1}{" " if self.apellido2 else ""}{self.apellido2}, {self.nombres}'

    def nombre_legal_ordenado(self):
        return (
            f'{self.nombres}'
            f'{f" {self.apellido1}" if self.apellido1 else ""}'
            f'{f" {self.apellido2}" if self.apellido2 else ""}'
        )

    def nombre_completo(self):
        return (
            f'{self.nombre()}'
            f'{f" {self.apellido1}" if self.apellido1 else ""}'
            f'{f" {self.apellido2[0]}." if self.apellido2 else ""}'
        )

    def documento(self):
        if self.tipo_identificacion == 0:
            return f'{self.numero_documento}-{self.digito_verificador}'

        return self.numero_documento

    def periodo_ingreso_uaysen(self):
        if not self.estudiantes.exists():
            return None

        # obtener periodo mínimo
        periodo_minimo = self.estudiantes.first().periodo_ingreso
        for estudiante in self.estudiantes.all()[1:]:
            if estudiante.periodo_ingreso < periodo_minimo:
                periodo_minimo = estudiante.periodo_ingreso

        return periodo_minimo

    def estudiante_activo(self):
        try:
            return self.estudiantes.get(estado_estudiante_id__in=(1, 4))
        except Estudiante.DoesNotExist:
            raise ValidationError(
                {'detail': 'el usuario no tiene un estudiante activo'},
            )
        except Estudiante.MultipleObjectsReturned:
            raise ValidationError(
                {'detail': 'el usuario tiene más de un estudiante activo'},
            )

    def __str__(self):
        return f'{self.documento()} {self.nombre_completo()}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__foto_antigua = self.foto

    def save(self, *args, **kwargs):
        # eliminar fotos antiguas
        if self.__foto_antigua and self.__foto_antigua != self.foto:
            storage = self.__foto_antigua.storage
            path = self.__foto_antigua.path
            storage.delete(path)

        # permitir mails nulos
        if not self.mail_institucional:
            self.mail_institucional = None

        # crear usuarios nuevos cuando sea necesario
        if not self.user_id:
            self.user, _ = User.objects.get_or_create(username=self.numero_documento)

        # actualizar usuario si es que se cambia el numero de documento
        elif self.user.username != self.numero_documento:
            self.user.username = self.numero_documento
            self.user.save()

        super().save(*args, **kwargs)


class EstadoEstudiante(models.Model):
    nombre = models.CharField(max_length=50, blank=True)

    id_ucampus = models.PositiveSmallIntegerField(null=True, blank=True)
    id_SAI = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'estado_estudiante'

    def __str__(self):
        return f'{self.nombre}'


class Estudiante(ModeloRegistraFechas):
    persona = models.ForeignKey('Persona', on_delete=models.PROTECT, related_name='estudiantes')
    plan = models.ForeignKey('academica.Plan', on_delete=models.PROTECT, related_name='estudiantes')
    estudiante_antiguo = models.ForeignKey(
        'self', on_delete=models.PROTECT, related_name='estudiantes_antiguos',
        null=True, blank=True,
        help_text='usado para mantener historial académico en cambios de carrera',
    )

    via_ingreso = models.ForeignKey(
        'matricula.ViaIngreso', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    periodo_ingreso = models.ForeignKey('curso.Periodo', on_delete=models.PROTECT, related_name='+')
    periodo_egreso = models.ForeignKey(
        'curso.Periodo', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    periodo_ingreso_uaysen = models.ForeignKey(
        'curso.Periodo', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    estado_estudiante = models.ForeignKey(
        'EstadoEstudiante', on_delete=models.PROTECT, related_name='+')

    habilitado = models.BooleanField(default=True)

    class Meta:
        db_table = 'estudiante'

    def __str__(self):
        return f'{self.persona} {self.plan}'

    def etapa_estudiante(self):
        etapas = EtapaEstudiante.objects.filter(estudiante=self, proceso_matricula__activo=True)

        if etapas.exists():
            return etapas.aggregate(ultima=Max('etapa_matricula__numero'))['ultima']

        return 0

    def registrar_etapa_matricula(self, etapa: int):
        EtapaEstudiante.objects.get_or_create(
            estudiante=self,
            etapa_matricula=EtapaMatricula.objects.get(numero=etapa),
            proceso_matricula=ProcesoMatricula.objects.get(activo=True)
        )
        return

    def es_estudiante_nuevo(self):
        ingreso_primer_anio = ProcesoMatricula.objects.get(activo=True).periodo_ingreso
        return self.periodo_ingreso == ingreso_primer_anio

    def es_estudiante_antiguo(self):
        return not self.es_estudiante_nuevo()

    def es_estudiante_pregrado(self):
        return self.plan.carrera.tipo_carrera == 0

    def es_estudiante_educontinua(self):
        return self.plan.carrera.tipo_carrera == 1

    def tipo_estudiante(self):
        """
        retorna el tipo del estudiante para determinar a qué periodo se debe

        0 = primer año
        1 = curso superior
        2 = educación continua
        """
        if self.es_estudiante_pregrado():
            if self.es_estudiante_nuevo():
                return 0

            if self.es_estudiante_antiguo():
                return 1

        if self.es_estudiante_educontinua():
            return 2

    def habilitado_matricula(self):
        if self.es_estudiante_pregrado():
            if self.es_estudiante_nuevo():
                return self.postulante.habilitado
            return True

        elif self.es_estudiante_educontinua():
            return self.postulanteeducontinua.habilitado

        return False

    def unidad_organizativa(self):
        if self.es_estudiante_pregrado():
            return 'Alumnos'

        elif self.es_estudiante_educontinua():
            return 'Alumnos Ed. Continua'

        raise Exception(
            f'No existe una unidad organizativa para estudiantes '
            f'de {self.plan.carrera.get_tipo_carrera_display()}'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.__estado_antiguo = self.estado_estudiante
        except EstadoEstudiante.DoesNotExist:
            self.__estado_antiguo = None

    @staticmethod
    def post_created(sender, instance, created, *args, **kwargs):
        # no registrar matrícula pendiente
        if instance.estado_estudiante.id == 6 and created:
            return

        # registrar cambios de estado
        if created or instance.__estado_antiguo != instance.estado_estudiante:
            HistorialEstadoEstudiante.objects.create(
                estudiante=instance,
                estado_estudiante=instance.estado_estudiante,
                periodo=Periodo.objects.get(activo=True)
            )
        return


post_save.connect(Estudiante.post_created, sender=Estudiante)


class HistorialEstadoEstudiante(ModeloRegistraFechas):
    """ registrado automáticamente al guardar estudiante """
    estudiante = models.ForeignKey(
        'Estudiante', on_delete=models.PROTECT, related_name='historial_estados')
    estado_estudiante = models.ForeignKey(
        'EstadoEstudiante', on_delete=models.PROTECT, related_name='+')
    periodo = models.ForeignKey('curso.Periodo', on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'historial_estado_estudiante'

    def __str__(self):
        return f'{self.estudiante} {self.estado_estudiante} {self.periodo}'
