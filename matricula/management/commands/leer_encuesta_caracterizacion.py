import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from matricula.models import EstudianteRespondeEncuesta
from mails.funciones import enviar_encuesta_respondida


class Command(BaseCommand):
    def handle(self, *args, **options):
        leer_encuestas()
        return


def leer_encuestas():
    apiKey = settings.QUESTIONPRO_APIKEY
    endpoint_parte1 = requests.get(f'https://api.questionpro.com/a/api/v2/surveys/10693135/responses?page=1&perPage=300&apiKey={apiKey}')
    endpoint_parte2 = requests.get(f'https://api.questionpro.com/a/api/v2/surveys/10696487/responses?page=1&perPage=300&apiKey={apiKey}')

    if (endpoint_parte1.status_code) == 200 and (endpoint_parte2.status_code == 200):
        json_endpoint1 = endpoint_parte1.json()
        lista_respuestas = json_endpoint1.get('response')

        # array de diccionarios con respuestas completadas (encuesta p1)
        # campos: responseID, user (persona.numero_documento) '''
        diccionarios_parte1 = []

        # listado de externalReference de respuestas completadas (parte2)
        # (apunta a responseIDs parte 1)
        lista_referencias_parte2 = []

        ruts_habilitados = []

        for respuesta in lista_respuestas:
            status = respuesta.get('responseStatus')
            if status == 'Completed':
                # obtener el id de respuesta y rut de las respuestas completadas
                qs = respuesta.get('responseSet')
                nro_doc_respuesta = qs[2].get('answerValues')[0].get('value').get('text')
                if '-' in nro_doc_respuesta:
                    parte_numerica = nro_doc_respuesta.split('-')[0]  # guarda hasta antes del guión
                    nro_doc_respuesta = parte_numerica
                nro_doc_respuesta = nro_doc_respuesta.replace("k", "").replace("K", "")
                id_respuesta = respuesta.get('responseID')

                registro = {'user': nro_doc_respuesta, 'responseID': id_respuesta}
                diccionarios_parte1.append(registro)

        #  lectura de JSON respuesta encuesta parte 2
        json_endpoint2 = endpoint_parte2.json()
        lista_respuestas = json_endpoint2.get('response')
        for respuesta in lista_respuestas:
            status = respuesta.get('responseStatus')
            if status == 'Completed':
                referencia = respuesta.get('externalReference')
                lista_referencias_parte2.append(referencia)

        for ref in lista_referencias_parte2:

            for respuesta_dict in diccionarios_parte1:
                if ref == str(respuesta_dict.get('responseID')):
                    try:
                        rut = int(respuesta_dict.get('user'))
                        ruts_habilitados.append(rut)
                    except ValueError:
                        print(f'hubo otro problema con el rut: ')
                        print(respuesta_dict.get('user'))
                        continue

        encuestas = EstudianteRespondeEncuesta.objects.filter(
            proceso_matricula__activo=True,
            estudiante__persona__numero_documento__in=ruts_habilitados,
            responde_encuesta=False,
        )
        for encuesta in encuestas:
            encuesta.responde_encuesta = True
            encuesta.save()
            print(f'enviando mail a {encuesta.estudiante}')
            enviar_encuesta_respondida(encuesta.estudiante)

    else:
        print("Hubo un problema con la conexión hacia la API de QuestionPro.")
        return
