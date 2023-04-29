from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection


class Command(BaseCommand):
    help = '''Reinicia las secuencias de llaves primarias para todos los modelos especificados'''

    def add_arguments(self, parser):
        parser.add_argument('modelos', type=str, nargs='+')

    def handle(self, *args, **options):
        print('reiniciando secuencias para los modelos', ', '.join(options['modelos']))

        modelos = []
        for modelo in options['modelos']:
            app, model = modelo.split('.')
            modelos.append(apps.get_model(app, model))

        sequence_sql = connection.ops.sequence_reset_sql(no_style(), modelos)
        with connection.cursor() as cursor:
            for sql in sequence_sql:
                cursor.execute(sql)
                print(sql)

        print('listo')
        return
