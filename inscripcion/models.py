from django.db import models
from django.utils import timezone


class ProcesoInscripcion(models.Model):
    nombre = models.CharField(max_length=50)
    periodo = models.ForeignKey('curso.Periodo', on_delete=models.PROTECT)

    fecha_apertura = models.DateTimeField()
    fecha_cierre = models.DateTimeField()

    # TODO: averiguar uso de este campo según reglamento
    tipos_inscripciones = [
        (0, 'regular'),
        (1, 'modifica'),
        (2, 'elimina'),
    ]
    tipo = models.PositiveSmallIntegerField(choices=tipos_inscripciones)
    estudiante = models.ManyToManyField('persona.Estudiante', blank=True)

    class Meta:
        db_table = 'proceso_inscripcion'
        unique_together = ('nombre', 'periodo')

    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_display()})'

    def get_estado(self):
        ahora = timezone.now()
        if ahora < self.fecha_apertura:
            return 0

        if ahora < self.fecha_cierre:
            return 1

        return 2

    def get_estado_display(self):
        ahora = timezone.now()
        if ahora < self.fecha_apertura:
            return 'pendiente'

        if ahora < self.fecha_cierre:
            return 'abierto'

        return 'cerrado'


class EnvioInscripcion(models.Model):
    persona = models.ForeignKey('persona.Persona', on_delete=models.PROTECT)
    proceso = models.ForeignKey('ProcesoInscripcion', on_delete=models.PROTECT)
    fecha_envio = models.DateTimeField(auto_now=True)

    felicidad = models.SmallIntegerField(default=0)

    class Meta:
        db_table = 'envio_inscripcion'
        unique_together = ('persona', 'proceso')

    def __str__(self):
        return f'{self.persona}'


class SolicitudCurso(models.Model):
    envio = models.ForeignKey(
        'EnvioInscripcion', on_delete=models.PROTECT, related_name='solicitudes')
    curso = models.ForeignKey('curso.Curso', on_delete=models.PROTECT, related_name='solicitudes')
    # solo utilizado en el caso de permutar
    curso2 = models.ForeignKey(
        'curso.Curso', null=True, blank=True, on_delete=models.PROTECT, related_name='+')

    prioridad = models.PositiveSmallIntegerField()

    tipos_solicitudes = [
        (0, 'agregar'),
        (1, 'eliminar'),
        (2, 'permutar'),
    ]
    tipo = models.PositiveSmallIntegerField(choices=tipos_solicitudes)

    estados = [
        (0, 'pendiente'),
        (1, 'aceptado'),
        (2, 'rechazado por cupo'),
        (3, 'rechazado por choque horario'),
        (4, 'rechazado por límite de créditos'),
        (5, 'curso ya inscrito para este semestre'),
        (6, 'pendiente aprobacion jefe de carrera'),
    ]
    estado = models.PositiveSmallIntegerField(choices=estados, default=0)

    class Meta:
        db_table = 'solicitud_curso'
        unique_together = ('envio', 'curso')
        unique_together = ('envio', 'prioridad', 'tipo')

    def __str__(self):
        return f'{self.envio} {self.get_tipo_display()} {self.curso} ({self.get_estado_display()})'
