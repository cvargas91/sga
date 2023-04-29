import csv
import os
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone

from matricula.models import ProcesoMatricula, MatriculaEstudiante


class Command(BaseCommand):
    help = '''
    Genera el reporte de matrícula DEMRE del proceso de matrícula activo y lo envía al correo
    especificado.
    '''

    def add_arguments(self, parser):
        parser.add_argument(
            'correos', metavar='correo', type=str, default=[],
            nargs='*',
            help='opcional: correos a los que enviar el reporte generado'
        )

    def handle(self, *args, **options):
        generar_reporte(correos=options['correos'])
        return


DIR_REPORTES = 'datos_estudiantes/reportes_matricula'

TIPOS_IDENTIFICACION = {
    0: 'C',
    1: 'P',
}

TIPOS_MATRICULAS = {
    1: 1,  # regular
    5: 2,  # repostulacion
    -1: 3,  # oficio de verificacion
    4: 4,  # BEA
    -2: 5,  # verificacion por acuerdo
    3: 6,  # PACE
    2: 7,  # admisión especial
    6: -1,  # trans externa
    7: -2,  # trans interna
}


def generar_reporte(correos):
    # asegurar que exista la carpeta
    if not os.path.exists(DIR_REPORTES):
        os.makedirs(DIR_REPORTES)

    hoy = timezone.localtime().strftime("%Y-%m-%d_%H-%M")
    nombre_archivo = f'{DIR_REPORTES}/reporte_{hoy}.csv'

    with open(nombre_archivo, 'w', newline='') as archivo_reporte:
        writer = csv.writer(archivo_reporte, delimiter=';')

        # insertar header
        writer.writerow([
            'TIPO_IDENTIFICACION',
            'NRO_IDENTIFICACION',
            'DIGITO_VERIFICADOR',
            'CODIGO_CARRERA',
            'TIPO_MATRICULA',
            'FECHA_MATRICULA',
            'HORA_MATRICULA',
            # 'VIA_INGRESO',
        ])

        proceso_activo = ProcesoMatricula.objects.get(activo=True)
        matriculas = MatriculaEstudiante.objects.filter(
            proceso_matricula=proceso_activo,
            estado=1,  # valido
            estudiante__periodo_ingreso=proceso_activo.periodo_ingreso,
        ).prefetch_related(
            'estudiante__persona',
            'estudiante__plan',
            'orden_compra',
        )
        matriculas_fecha = matriculas.order_by('orden_compra__fecha_pago')

        for matricula in matriculas_fecha:
            fecha_pago = timezone.localtime(matricula.orden_compra.fecha_pago)
            if not fecha_pago:
                print(
                    f'fecha de pago no definida, utilizando fecha de creación para '
                    f'la orden de compra {matricula.orden_compra.id}'
                )
                fecha_pago = matricula.orden_compra.creado
            if matricula.estudiante.via_ingreso_id != 6:
                writer.writerow([
                    TIPOS_IDENTIFICACION[matricula.estudiante.persona.tipo_identificacion],
                    matricula.estudiante.persona.numero_documento,
                    matricula.estudiante.persona.digito_verificador,
                    matricula.estudiante.plan.codigo_demre,
                    TIPOS_MATRICULAS[matricula.estudiante.via_ingreso.id],
                    fecha_pago.strftime("%d/%m/%Y"),
                    fecha_pago.strftime("%H:%M"),
                    # matricula.estudiante.via_ingreso.nombre,
                ])

    print(f'reporte generado y almacenado en {nombre_archivo}')

    if correos:
        print(f'enviando a los correos: {", ".join(correos)}')

        email = EmailMessage(
            subject=f'Reporte matrícula DEMRE {hoy}',
            body='',
            to=correos,
            from_email=settings.EMAIL_HOST_USER,
            reply_to=[settings.EMAIL_HOST_USER],
        )
        email.attach_file(nombre_archivo)

        try:
            email.send()
        except SMTPException:
            print('ha habido un error al intentar enviar el mail.')

    return
