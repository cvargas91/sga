from django.core.management.base import BaseCommand
from matricula.models import PostulanteDefinitivo, ProcesoMatricula


class Command(BaseCommand):
    def handle(self, *args, **options):
        rectificar()
        return


def rectificar():

    # seleccionar postulantes definitivos de éste año
    # postulante definitivo:
    # obtener su persona
    # obtener fecha de nacimiento
    # castear a %dd %mm %AAAA (debe ser de 8 digitos)
    # reemplazar postulantedefinitivo.numero_demre por fecha casteada
    # si no tienen fecha de nacimiento (especial/transferencia externa) usar numero de documento

    proceso_matricula = ProcesoMatricula.objects.get(activo=True)
    postulantes = PostulanteDefinitivo.objects.filter(proceso_matricula=proceso_matricula)

    contador_ok = 0
    contador_nulos = 0
    for postulante in postulantes:
        persona = postulante.persona
        fecha = persona.fecha_nacimiento
        try:
            fecha_casteada = fecha.strftime('%d%m%Y')
            postulante.numero_demre = fecha_casteada
            postulante.save()
            contador_ok += 1
        except AttributeError:  # campo fecha nulo
            postulante.numero_demre = persona.numero_documento
            postulante.save()
            contador_nulos += 1
    print(f'se actualizo el numero_demre de {contador_ok} postulantes a su fecha nacimiento ddmmAAAA')
    print(f'se actualizo el numero_demre de {contador_nulos} postulantes a su numero documento')

    return
