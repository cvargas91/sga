import os
import secrets
import string

from django.db import models
from django.conf import settings


def dir_certificados():
    return os.path.join(settings.MEDIA_ROOT, 'certificados')


def generar_llave(largo=12):
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for x in range(largo))


class Certificado(models.Model):
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=models.PROTECT)

    llave = models.CharField(max_length=12, default=generar_llave)
    valido = models.BooleanField(default=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)

    tipos_certificado = [
        (0, 'estudiante regular'),
        (1, 'matrícula'),
        (2, 'notas'),
        (3, 'personalizado')
    ]
    tipo_certificado = models.PositiveSmallIntegerField(choices=tipos_certificado, default=0)
    archivo = models.FilePathField(path=dir_certificados, null=True)

    class Meta:
        db_table = 'certificado'

    def __str__(self):
        return f'{self.get_tipo_certificado_display()} - {self.estudiante}'

    @property
    def nombre_archivo(self):
        if self.archivo is None:
            return None
        return os.path.split(self.archivo)[1]

    @property
    def url_archivo(self):
        if self.nombre_archivo is None:
            return None
        return f'{settings.URL_BACKEND}{settings.MEDIA_URL}certificados/{self.nombre_archivo}'


class SolicitudCertificado(models.Model):
    estudiante = models.ForeignKey('persona.Estudiante', on_delete=models.PROTECT)
    titulo = models.CharField(max_length=60)
    descripcion = models.TextField()
    justificacion = models.TextField()

    titulo_revisor = models.CharField(max_length=60, null=True, blank=True)
    contenido_revisor = models.TextField(null=True, blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    certificado = models.ForeignKey('Certificado', null=True, blank=True, on_delete=models.PROTECT)
    estados_solicitud = [
        (0, 'pendiente'),
        (1, 'aceptada'),
        (2, 'rechazada')
    ]
    estado = models.PositiveSmallIntegerField(choices=estados_solicitud, default=0)

    class Meta:
        db_table = 'solicitud_certificado'

    def __str__(self):
        return f'Solicitud {self.titulo} - {self.estudiante}'
