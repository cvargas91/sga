from django.core.management.base import BaseCommand

from mails.funciones import enviar_confirmacion_matricula, enviar_encuesta_respondida
from persona.models import Estudiante
from certificados.models import Certificado
from matricula.models import ProcesoMatricula


class Command(BaseCommand):

    def handle(self, *args, **options):
        periodo_ingreso_actual = ProcesoMatricula.objects.get(activo=True).periodo_ingreso
        estudiante_nuevo = Estudiante.objects.filter(
            periodo_ingreso=periodo_ingreso_actual,
        ).filter(
            estado_estudiante_id__in=[4, 1],  # regular o congelado
        ).first()

        # incluir un certificado si es que existe alguno
        certificado = None
        if Certificado.objects.all().exists():
            certificado = Certificado.objects.first()

        print('enviando mail matrícula estudiante nuevo...')
        enviar_confirmacion_matricula(
            estudiante=estudiante_nuevo,
            contrasena='prueba constraseña',
            certificado=certificado,
        )
        print('mail enviado correctamente')

        print('\nenviando mail encuesta...')
        enviar_encuesta_respondida(
            estudiante=estudiante_nuevo,
        )
        print('mail enviado correctamente')

        estudiante_antiguo = Estudiante.objects.exclude(
            periodo_ingreso=periodo_ingreso_actual,
        ).filter(
            estado_estudiante_id__in=[4, 1],  # regular o congelado
        ).first()
        print('\nenviando mail matrícula estudiante antiguo...')
        enviar_confirmacion_matricula(
            estudiante=estudiante_antiguo,
        )
        print('mail enviado correctamente')
        return
