import os
import pyqrcode
from collections import OrderedDict

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf import pisa
from babel.dates import format_date

from certificados.models import Certificado, dir_certificados
from curso.models import EstudianteCurso, Periodo


def crear_certificado_estudiante_regular(estudiante) -> Certificado:
    certificado = Certificado.objects.create(
        estudiante=estudiante,
        tipo_certificado=0,  # estudiante regular
    )

    # generar documento
    contexto = contexto_certificado(certificado=certificado)
    contexto['estudiante'] = estudiante
    contexto['periodo'] = Periodo.objects.get(activo=True)

    generar_doc_certificado(
        certificado=certificado,
        nombre_archivo=f'regular_{certificado.id}_{estudiante.persona.numero_documento}.pdf',
        template='estudiante_regular.html',
        contexto=contexto,
    )
    return certificado


def crear_certificado_matricula(estudiante) -> Certificado:
    certificado = Certificado.objects.create(
        estudiante=estudiante,
        tipo_certificado=1,  # matrícula
    )

    # generar documento
    contexto = contexto_certificado(certificado=certificado)
    contexto['estudiante'] = estudiante
    contexto['ano'] = 2023

    generar_doc_certificado(
        certificado=certificado,
        nombre_archivo=f'matricula_{certificado.id}_{estudiante.persona.numero_documento}.pdf',
        template='matricula.html',
        contexto=contexto,
    )
    return certificado


def crear_certificado_notas(estudiante) -> Certificado:
    certificado = Certificado.objects.create(
        estudiante=estudiante,
        tipo_certificado=2,  # notas
    )

    # obtener cursos completados
    cursos = EstudianteCurso.objects.filter(
        estudiante=estudiante, estado__completado=True,
    ).order_by('curso__periodo')

    # ordenar cursos por periodo
    periodos = OrderedDict()  # mantiene el orden en que se ingresan las llaves
    for curso in cursos:
        periodo = curso.curso.periodo
        # if periodo not in periodos:
        #     periodos[periodo] = {
        #         'cursos': [],
        #         'promedio': None
        #     }
        # periodos[periodo]['cursos'].append(curso)
        periodo_id = periodo.id

        if periodo_id not in periodos:
            periodos[periodo_id] = {
                'cursos': [],
                'promedio': None,
            }
        periodos[periodo_id]['cursos'].append(curso)

    # calcular promedio por periodo
    for periodo in periodos:
        cursos = [curso for curso in periodos[periodo]['cursos'] if curso.estado.aprobado]
        if len(cursos) > 0:
            promedio = sum(curso.nota_final for curso in cursos) / len(cursos)
            periodos[periodo]['promedio'] = round(promedio, 2)

    # generar documento
    contexto = contexto_certificado(certificado=certificado)
    contexto['estudiante'] = estudiante
    contexto['ano'] = Periodo.objects.get(activo=True).ano
    contexto['periodos'] = periodos
    generar_doc_certificado(
        certificado=certificado,
        nombre_archivo=f'notas_{certificado.id}_{estudiante.persona.numero_documento}.pdf',
        template='notas.html',
        contexto=contexto,
    )

    return certificado


def crear_certificado_personalizado(estudiante, titulo, contenido) -> Certificado:
    certificado = Certificado.objects.create(
        estudiante=estudiante,
        tipo_certificado=3
    )

    contexto = contexto_certificado(certificado=certificado)
    contexto['titulo'] = titulo
    contexto['contenido'] = contenido

    generar_doc_certificado(
        certificado=certificado,
        nombre_archivo=f'personalizado_{certificado.id}_'
                       f'{estudiante.persona.numero_documento}.pdf',
        template='personalizado.html',
        contexto=contexto,
    )
    return certificado


# contexto común para todos los certificados que usan el template base_certificados.html
def contexto_certificado(certificado: Certificado) -> dict:
    folio = certificado.id
    llave = certificado.llave

    # url de validación, quitar '?' para optimizar codificación
    qr_url = f'{settings.URL_FRONTEND_MATRICULA}/validar/{folio}/{llave}'

    # generar código qr como un string base 64, utilizar mayúsculas para optimizar la codificación
    qr_base64 = pyqrcode.create(qr_url.upper(), error='M').png_as_base64_str(scale=5)

    fecha = format_date(certificado.fecha_emision, format="EEEE d 'de' MMMM 'del' y", locale='es')
    return {
        'fecha': fecha,
        'qr_url': qr_url,
        'qr_base64': qr_base64,
    }


def generar_doc_certificado(
    certificado: Certificado,
    nombre_archivo: str,
    template: str,
    contexto: dict,
):
    # asegurar que exista la carpeta
    if not os.path.exists(dir_certificados()):
        os.makedirs(dir_certificados())

    path_certificado = os.path.join(dir_certificados(), nombre_archivo)

    with open(path_certificado, "w+b") as archivo:
        template = get_template(template)
        html = template.render(contexto)
        pisa.CreatePDF(html, dest=archivo, link_callback=link_callback)

    certificado.archivo = path_certificado
    certificado.save()
    return


def previsualizar_certificado(
    template_path: str,
    contexto: dict,
):
    # agregar contexto necesario
    qr_url = f'{settings.URL_FRONTEND_MATRICULA}/validar/123456/loremipsum'
    contexto['fecha'] = 'lunes 00 de MES del YYYY'
    contexto['qr_url'] = qr_url
    contexto['qr_base64'] = pyqrcode.create(qr_url.upper(), error='M').png_as_base64_str(scale=5)

    # crear la respuesta
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="previsualizacion_certificado.pdf"'
    html = get_template(template_path).render(contexto)
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)

    if pisa_status.err:
        return HttpResponse(f'We had some errors <pre>{html}</pre>')

    return response


def link_callback(uri, rel):
    """
    Convierte urls de Django media/static a su path absoluto en el sistema
    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:  # no es una url de django
        return uri

    # asegurar que el archivo existe
    if not os.path.isfile(path):
        raise Exception(f'no se ha encontrado el archivo {path} (url original: {uri})')

    return path
