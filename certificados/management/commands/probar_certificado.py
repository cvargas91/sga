from django.core.management.base import BaseCommand

from persona.models import Persona
from certificados.generador import crear_certificado_matricula


class Command(BaseCommand):
    def handle(self, *args, **options):
        persona = Persona.objects.get(numero_documento=72459)
        cert = crear_certificado_matricula(estudiante=persona.estudiantes.first())
        print(f'certificado generado y disponible en {cert.url_archivo}')
        return
