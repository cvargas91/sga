import os
from io import BytesIO
from django.utils import timezone
from django.conf import settings
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER
from matricula.models import PostulanteDefinitivo

from persona.models import Estudiante, Persona, dir_contratos


def generar_contrato(persona: Persona):

    nombre = persona.nombre_legal_ordenado()
    nro_doc = persona.numero_documento
    dv = persona.digito_verificador
    try:
        postulante = PostulanteDefinitivo.objects.get(
            persona=persona, habilitado=True, resultado_postulacion=0)
        carrera = postulante.plan.carrera.nombre
    except PostulanteDefinitivo.DoesNotExist:
        estudiante = Estudiante.objects.filter(persona=persona).last()
        carrera = estudiante.plan.carrera.nombre

    fecha_hora = timezone.localtime().strftime("%d-%m-%Y a las %H:%M hrs")
    # directorio_contrato = os.path.join(settings.STATIC_ROOT, 'documentos')
    # ruta_archivo_contrato = os.path.join(directorio_contrato, 'contrato.pdf')
    # contrato_original = PdfReader(ruta_archivo_contrato)
    contrato_original = PdfReader('contrato.pdf')

    pagina1 = contrato_original.pages[0]
    pagina2 = contrato_original.pages[1]
    pagina3 = contrato_original.pages[2]

    buffer = BytesIO()
    canvas_firma = canvas.Canvas(buffer)

    texto = f'''Leído y aceptado por {nombre} RUN {nro_doc}-{dv} el día {fecha_hora} a
                 través del portal https://matricula.uaysen.cl durante el
                 proceso de matrícula a la carrera de {carrera}'''

    estilos = ParagraphStyle('Custom',                  # nombre del estilo
                             fontName='Helvetica-Bold',
                             fontSize=16,
                             alignment=TA_CENTER,
                             leading=16)                # interlineado

    parrafo = Paragraph(texto, estilos)

    parrafo.wrapOn(canvas_firma, 500, 200)    # espacio en x,y del canvas donde fluye el párrafo
    parrafo.drawOn(canvas_firma, 50, 100)     # punto de inicio en x,y donde se dibuja el párrafo
    canvas_firma.save()

    buffer.seek(0)
    lector_canvas = PdfReader(buffer)
    pagina_firma = lector_canvas.pages[0]

    salida = PdfWriter()
    salida.add_page(pagina1)
    salida.add_page(pagina2)

    pagina3.merge_page(pagina_firma)

    salida.add_page(pagina3)

    if not os.path.exists(dir_contratos()):
        os.makedirs(dir_contratos())
    path_contrato = os.path.join(dir_contratos(), f'contrato_{nro_doc}.pdf')
    persona.archivo_contrato = path_contrato
    persona.save()
    with open(path_contrato, "wb") as output_stream:
        salida.write(output_stream)
