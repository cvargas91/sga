import csv
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db.utils import IntegrityError

from persona.models import Persona, Estudiante
from academica.models import Plan
from matricula.models import (
    ProcesoMatricula, ValorMatricula, MatriculaEstudiante, ArancelEstudiante, ValorArancel,
    TNEEstudiante, PostulanteEducacionContinua,
)
from pagos.models import (
    Productos, FormaPago, OrdenCompra, OrdenCompraDetalle,
)


class Command(BaseCommand):
    help = '''Importa a los postulantes en el archivo entregado'''

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str)

        parser.add_argument(
            '--completar-proceso',
            action='store_true',
            help='carga a los estudiantes como si ya hubieran completado el proceso de matrícula',
        )

    def handle(self, *args, **options):
        importar_postulantes(options['archivo'], options['completar_proceso'])
        return


def importar_postulantes(archivo: str, completar_proceso: bool = False):
    proceso = ProcesoMatricula.objects.get(activo=True)
    print('Cargando Postulantes...')
    with open(archivo, 'r', encoding='utf8') as archivo_postulantes:
        postulantes = csv.DictReader(archivo_postulantes, delimiter=',')

        tipos_identificacion = {
            '': 0,
            'C': 0,  # rut
            'P': 1,  # pasaporte
        }
        sexos = {
            '': 2,  # no especifica
            'masculino': 1,  # masculino
            'femenino': 0,  # femenino
        }
        tipos_dcto = {
            'fijo': 0,  # masculino
            'porcentual': 1,  # femenino
        }
        for fila in postulantes:
            print(f'El rut es {fila}')
            usuario, creado = User.objects.get_or_create(username=fila['RUT'])

            if not Persona.objects.filter(user=usuario).exists():
                persona = Persona(
                    user=usuario,
                    tipo_identificacion=tipos_identificacion[fila['TIPO_DOCUMENTO']],
                    numero_documento=fila['RUT'],
                    digito_verificador=fila['DV'],

                    apellido1=fila['APELLIDO PAT'].title(),
                    apellido2=fila['APELLIDO MAT'].title(),
                    nombres=fila['NOMBRE'].title(),
                    sexo=sexos[fila['SEXO']],

                    telefono_celular=fila['TELEFONO_CELULAR'],
                    mail_secundario=fila['EMAIL_PERSONAL'],
                    mail_institucional=fila['EMAIL_UAYSEN'],
                )

                fecha = fila['FECHA_NACIMIENTO']
                if fecha:
                    try:
                        persona.fecha_nacimiento = datetime.strptime(fecha, '%d/%m/%Y')
                    except ValueError:
                        print(f'no se pudo parsear la fecha {fecha}')

                persona.save()

            else:
                # persona ya existe, actualizar campos
                persona = Persona.objects.get(user=usuario)
                persona.tipo_identificacion = tipos_identificacion[fila['TIPO_DOCUMENTO']]
                persona.numero_documento = fila['RUT']
                persona.digito_verificador = fila['DV']

                persona.apellido1 = fila['APELLIDO PAT'].title()
                persona.apellido2 = fila['APELLIDO MAT'].title()
                persona.nombres = fila['NOMBRE'].title()
                persona.sexo = sexos[fila['SEXO']]

                persona.mail_institucional = fila['EMAIL_UAYSEN']
                persona.mail_secundario = fila['EMAIL_PERSONAL']
                persona.telefono_celular = fila['TELEFONO_CELULAR']

                fecha = fila['FECHA_NACIMIENTO']
                if fecha:
                    try:
                        persona.fecha_nacimiento = datetime.strptime(fecha, '%d/%m/%Y')
                    except ValueError:
                        print(f'no se pudo parsear la fecha {fecha}')

                persona.save()

            resultados = {
                '0': 0,  # seleccionado
                '1': 1,
                # '24': 0,  # seleccionado
                # '25': 1,  # lista de espera
            }
            try:
                plan = Plan.objects.get(carrera__nombre=fila['NOMBRE_PROGRAMA'])
                postulante = PostulanteEducacionContinua(
                    persona=persona,
                    proceso_matricula=proceso,
                    plan=plan,
                    clave=fila['RUT'],
                    resultado_postulacion=resultados[fila['RESULTADO_POSTULACION']],
                    posicion_lista=fila['POSICION_LISTA'],
                    habilitado=True,
                    tipo_descuento_matricula=tipos_dcto.get(fila['TIPO_DCTO_MAT'], None),
                    monto_descuento_matricula=fila['DCTO_MAT'],
                    descripcion_descuento_matricula=fila['DESCRIPCION_DCTO_MAT'],
                    tipo_descuento_arancel=tipos_dcto.get(fila['TIPO_DCTO_ARANCEL'], None),
                    monto_descuento_arancel=fila['DCTO_ARANCEL'],
                    descripcion_descuento_arancel=fila['DESCRIPCION_DCTO_ARANCEL'],
                )
                postulante.save()

            except Plan.DoesNotExist:
                print(f'plan con nombre { fila["NOMBRE_PROGRAMA"] } no existe')
                return

            except IntegrityError:
                print(f'postulante { fila["RUT"] } - {plan} ya existe')
                return

            if completar_proceso:
                # aceptar vacante
                estudiante = Estudiante(
                    plan=postulante.plan,
                    persona=postulante.persona,
                    periodo_ingreso=proceso.periodo_ingreso,
                    estado=0,  # estudiante regular
                )
                estudiante.save()

                postulante.acepta_vacante = True
                postulante.estudiante = estudiante
                postulante.save()
                estudiante.registrar_etapa_matricula(etapa=1)

                valor_matricula = ValorMatricula.objects.get(
                    proceso_matricula=proceso,
                    plan=estudiante.plan,
                )
                matricula_estudiante = MatriculaEstudiante(
                    proceso_matricula=proceso,
                    estudiante=estudiante,
                    monto_final=valor_matricula.valor,
                    estado=1,
                )
                matricula_estudiante.save()

                tne = TNEEstudiante(proceso_matricula=proceso, estudiante=estudiante)
                tne.save()

                valor_plan = ValorArancel.objects.get(
                    proceso_matricula=proceso,
                    plan=postulante.plan,
                )
                arancel_estudiante = ArancelEstudiante(
                    proceso_matricula=proceso,
                    estudiante=estudiante,
                    valor_arancel=valor_plan,
                    monto=valor_plan.valor,
                )
                arancel_estudiante.save()

                # datos personales
                estudiante.registrar_etapa_matricula(etapa=2)

                # pago matrícula
                orden_compra = OrdenCompra(
                    persona=estudiante.persona,
                    forma_pago=FormaPago.objects.get(id=1),  # caja
                    monto_total=0,
                    total_descuento_beneficios=0,
                    estado_pago=1,
                    estado=True,
                )
                orden_compra.save()
                matricula_estudiante.orden_compra = orden_compra
                matricula_estudiante.save()

                producto_matricula = Productos.objects.get(
                    codigo_interno=proceso.id,  # referencia proceso
                    categoria_id=1,  # correspondiente a "proceso" matricula 2021
                    subcategoria_id=1  # correspondiente a "producto" matricula 2021
                )
                orden_compra_detalle = OrdenCompraDetalle(
                    orden_compra=orden_compra,
                    producto=producto_matricula,
                    valor=producto_matricula.valor,
                    cantidad=1,
                    descuento=0,
                )
                orden_compra_detalle.save()

                estudiante.registrar_etapa_matricula(etapa=3)

                # pago arancel
                orden_compra = OrdenCompra(
                    persona=estudiante.persona,
                    forma_pago=FormaPago.objects.get(id=1),  # caja
                    monto_total=0,
                    total_descuento_beneficios=0,
                    estado_pago=1,
                    estado=True,
                )
                orden_compra.save()
                arancel_estudiante.orden_compra = orden_compra
                arancel_estudiante.save()

                producto_arancel = Productos.objects.get(
                    codigo_interno=plan.id,  # referencia valor_matricula
                    categoria_id=1,  # correspondiente a "proceso" matricula 2021
                    subcategoria_id=3  # correspondiente a "producto" Arancel 2021
                )
                orden_compra_detalle = OrdenCompraDetalle(
                    orden_compra=orden_compra,
                    producto=producto_arancel,
                    valor=producto_arancel.valor,
                    cantidad=1,
                    descuento=0,
                )
                orden_compra_detalle.save()
                estudiante.registrar_etapa_matricula(etapa=4)
    return
