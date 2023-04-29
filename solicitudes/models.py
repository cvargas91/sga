from datetime import timedelta
from django.db import models
from django.db.models.deletion import PROTECT
from django.db.models.fields import IntegerField

from general.models import ModeloRegistraFechas


# Create your models here.
class Solicitud(models.Model):
    estados_solicitud = [
        (0, 'Pendiente'),
        (1, 'Aprobada'),
        (2, 'Rechazada'),
        (3, 'No Procede'),
        (4, 'Expirada'),
        (5, 'Renuncia Pendiente')
    ]
    tipo = models.ForeignKey('TipoSolicitud', on_delete=PROTECT)
    causas_estudiante = models.ManyToManyField('CausaSolicitud', related_name='causas_estudiante')
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=PROTECT)
    periodo = models.ForeignKey('curso.Periodo', on_delete=PROTECT)
    fecha_creacion = models.DateField(auto_now_add=True)
    fecha_actualizacion = models.DateField(auto_now=True)
    fecha_resolucion = models.DateField(blank=True, null=True)
    justificacion_estudiante = models.TextField()
    estado = models.PositiveSmallIntegerField(choices=estados_solicitud, default=0)
    resolucion = models.CharField(max_length=16, blank=True)
    comentario_revisor = models.TextField(blank=True)
    justificacion_revisor = models.TextField(blank=True)
    valida_causas = models.BooleanField(blank=True, null=True)
    causas_revisor = models.ManyToManyField('CausaSolicitud', related_name='causas_revisor',
                                            blank=True)

    class Meta:
        db_table = 'solicitud'

    def __str__(self):
        return f'Solicitud {self.tipo} {self.estudiante}'


class TipoSolicitud(models.Model):
    nombre = models.CharField(max_length=100)
    instrucciones = models.CharField(max_length=500)
    estados_validos = models.ManyToManyField('persona.EstadoEstudiante')
    plazo_resolucion = models.DurationField(default=timedelta(weeks=12), null=True)

    class Meta:

        db_table = 'tipo_solicitud'

    def __str__(self):
        return self.nombre


class PeriodoTipoSolicitud(ModeloRegistraFechas):
    tipo_solicitud = models.ForeignKey('TipoSolicitud', on_delete=models.PROTECT)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()

    def __str__(self):
        return f'Periodo {self.tipo_solicitud } {self.fecha_inicio} - {self.fecha_fin}'


class CausaSolicitud(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = 'causa_solicitud'

    def __str__(self):
        return self.nombre


class SolicitudCambioCarrera(models.Model):
    solicitud = models.OneToOneField(Solicitud, on_delete=PROTECT)
    carrera = models.ForeignKey('academica.Carrera', on_delete=PROTECT)

    class Meta:
        db_table = 'solicitud_cambio_carrera'


class SolicitudPostergacion(models.Model):
    solicitud = models.OneToOneField(Solicitud, on_delete=PROTECT)
    duracion_semestres = IntegerField(choices=[(1, '1'), (2, '2')])

    class Meta:
        db_table = 'solicitud_postergacion'


class SolicitudReintegracion(models.Model):
    solicitud = models.OneToOneField(Solicitud, on_delete=PROTECT)

    class Meta:
        db_table = 'solicitud_reintegracion'


class SolicitudRenuncia(models.Model):
    solicitud = models.OneToOneField(Solicitud, on_delete=PROTECT)

    class Meta:
        db_table = 'solicitud_renuncia'
