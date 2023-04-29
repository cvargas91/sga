from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.conf import settings

import os
from email.mime.image import MIMEImage
from smtplib import SMTPException


def crear_email(asunto, contenido, receptores):
    email = EmailMessage(
        subject=asunto,
        body=contenido,
        to=receptores,
        from_email=settings.EMAIL_HOST_USER,
        reply_to=[settings.EMAIL_HOST_USER],
    )
    email.content_subtype = 'html'

    # adjuntar logo
    with open(os.path.join(settings.BASE_DIR, 'static/logo_azul.png'), mode='rb') as archivo:
        imagen = MIMEImage(archivo.read())
        imagen.add_header('Content-ID', '<logo_uaysen>')
        email.attach(imagen)

    return email


def email_pruebas(numero_documento: str):
    return f'+{numero_documento}@'.join(settings.EMAIL_HOST_USER.split('@'))


def enviar_confirmacion_matricula(estudiante, contrasena=None, certificado=None):
    contexto = {
        'nombre': estudiante.persona.nombre(),
        'carrera': estudiante.plan.carrera.nombre,
        'mail': estudiante.persona.mail_institucional,
        'contrasena': contrasena,
        'certificado': certificado is not None,
        'tipo_estudiante': estudiante.tipo_estudiante(),
    }
    contenido = get_template('confirmacion_matricula.html').render(contexto)

    receptores = [
        estudiante.persona.mail_secundario
    ]
    if estudiante.plan.carrera.tipo_carrera == 0:  # enviar copia a secretaría académica (pregrado)
        receptores.append('secretaria.academica@uaysen.cl')

    if settings.DEBUG:
        receptores = [email_pruebas(estudiante.persona.numero_documento)]

    email = crear_email(
        asunto='Confirmación de Matrícula',
        contenido=contenido,
        receptores=receptores,
    )

    # adjuntar certificado
    if certificado is not None:
        email.attach_file(certificado.archivo)

    # adjuntar contrato firmado para todos los estudiantes (2024 debería limitarse a alumnos nuevos)
    if estudiante.persona.archivo_contrato is not None:
        email.attach_file(estudiante.persona.archivo_contrato)
    try:
        email.send()
    except SMTPException:
        print('ha habido un error al intentar enviar el mail.')
    return


def enviar_encuesta_respondida(estudiante):
    contexto = {
        'nombre': estudiante.persona.nombre(),
    }
    contenido = get_template('encuesta_respondida.html').render(contexto)

    receptor = estudiante.persona.mail_institucional
    if settings.DEBUG:
        receptor = email_pruebas(estudiante.persona.numero_documento)

    email = crear_email(
        asunto='Encuesta de caracterización respondida',
        contenido=contenido,
        receptores=[receptor],
    )

    try:
        email.send()
    except SMTPException:
        print('ha habido un error al intentar enviar el mail.')
    return
