from django.contrib import admin
from django.utils import timezone

from .models import (
    ProcesoMatricula, PeriodoProcesoMatricula, PostulanteDefinitivo, EtapaEstudiante,
    ValorMatricula, ValorArancel, ArancelEstudiante, InhabilitantesMatricula,
    MatriculaEstudiante, TNEEstudiante, GratuidadEstudiante, EstudianteRespondeEncuesta,
    PostulanteEducacionContinua,
)


admin.site.register(ProcesoMatricula)


@admin.register(PeriodoProcesoMatricula)
class PeriodoProcesoMatriculaAdmin(admin.ModelAdmin):
    list_display = [
        'descripcion',
        'fecha_inicio',
        'fecha_fin',
        'publico',
        'carreras',
    ]

    list_filter = ['proceso_matricula']

    def carreras(self, obj):
        carreras = obj.planes.values_list('carrera__nombre', flat=True)
        return ', '.join(carreras)


@admin.register(ValorMatricula)
class ValorMatriculaAdmin(admin.ModelAdmin):
    list_display = [
        'proceso_matricula',
        'plan',
        'valor',
    ]

    list_filter = ['proceso_matricula', 'plan']


@admin.register(ValorArancel)
class ValorArancelAdmin(admin.ModelAdmin):
    list_display = [
        'proceso_matricula',
        'plan',
        'valor',
    ]

    list_filter = ['proceso_matricula']


class FiltroEtapa(admin.SimpleListFilter):
    title = 'etapa actual'
    parameter_name = 'etapa'

    def lookups(self, request, model_admin):
        return (
            (1, 'Acepta Vacante'),
            (2, 'Datos de Contacto'),
            (3, 'Pago de Matrícula'),
            (4, 'Pago de Arancel'),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        etapa = int(self.value())

        # obtener todos los que están en una etapa más avanzada
        avanzados = EtapaEstudiante.objects.filter(
            etapa_matricula__numero=etapa + 1,
        ).values_list('estudiante')

        # obtener todos los que están en la etapa actual pero no en una más avanzada
        ids_estudiantes = EtapaEstudiante.objects.filter(
            etapa_matricula__numero=etapa,
        ).exclude(
            estudiante__in=avanzados,
        ).values_list('estudiante')

        # filtrar
        return queryset.filter(estudiante__in=ids_estudiantes)


@admin.register(PostulanteDefinitivo)
class PostulanteDefinitivoAdmin(admin.ModelAdmin):
    list_display = [
        'nro_documento',
        'nombre',
        'plan',
        'habilitado',
        'via_ingreso',
        'posicion_lista',
        'resultado',
        'gratuidad',
        'etapa',
        'regular',
    ]

    list_select_related = [
        'persona',
    ]

    list_filter = [
        'proceso_matricula',
        'plan',
        'via_ingreso',
        'resultado_postulacion',
        FiltroEtapa,
    ]

    list_select_related = ('persona', 'estudiante')

    search_fields = ['persona__numero_documento', 'persona__nombres', 'persona__apellido1']

    autocomplete_fields = ['persona']

    fieldsets = [
        (None, {
            'fields': ['persona', 'proceso_matricula', 'plan', 'habilitado']
        }),
        ('Datos ingreso', {
            'fields': [
                'via_ingreso', 'PACE', 'numero_demre', 'resultado_postulacion', 'posicion_lista',
                'preseleccionado_gratuidad',
            ]
        }),
        ('Datos Matrícula', {
            'classes': ('collapse',),  # no mostrar por defecto
            'fields': [
                'acepta_vacante', 'estudiante', 'etapa', 'regular'
            ]
        }),
        ('Puntajes', {
            'classes': ('collapse',),  # no mostrar por defecto
            'fields': [
                'promedio_NEM', 'puntaje_NEM', 'puntaje_ranking', 'puntaje_matematica',
                'puntaje_lenguaje', 'promedio_lenguaje_matematica', 'percentil_lenguaje_matematica',
                'puntaje_historia', 'modulo_ciencias', 'puntaje_ciencias', 'puntaje_ponderado',
                'puntaje_matematica_m1', 'puntaje_matematica_m2'
            ]
        }),
    ]

    readonly_fields = [
        'etapa', 'regular',
    ]

    def get_readonly_fields(self, request, obj):
        if request.user.is_superuser and obj is not None:
            return super().get_readonly_fields(request, obj)

        return self.readonly_fields + ['acepta_vacante', 'estudiante']

    def nombre(self, obj):
        return obj.persona.nombre_completo()
    nombre.admin_order_field = 'persona__apellido1'

    def nro_documento(self, obj):
        return obj.persona.documento()
    nro_documento.admin_order_field = 'persona__numero_documento'

    def gratuidad(self, obj):
        return obj.preseleccionado_gratuidad
    gratuidad.admin_order_field = 'preseleccionado_gratuidad'
    gratuidad.boolean = True

    def resultado(self, obj):
        return obj.get_resultado_postulacion_display()
    resultado.admin_order_field = 'resultado_postulacion'

    def etapa(self, obj):
        return obj.etapa_actual()

    def regular(self, obj):
        if obj.estudiante:
            return obj.estudiante.estado_estudiante_id == 4
    regular.boolean = True

    actions = ['habilitar_postulantes', 'deshabilitar_postulantes']

    def habilitar_postulantes(self, request, queryset):
        queryset.update(habilitado=True)
    habilitar_postulantes.allowed_permissions = ('view',)

    def deshabilitar_postulantes(self, request, queryset):
        queryset.update(habilitado=False)
    deshabilitar_postulantes.allowed_permissions = ('view',)


class AdminRelacionEstudiante(admin.ModelAdmin):
    """
    Super clase para todos los modelos que se relacionan con estudiante.

    Agrega numero de documento, nombre y plan al listado, filtro por plan y búsqueda por documento.
    """
    list_display = [
        'documento',
        'ano',
        'nombre',
        'plan',
    ]

    list_select_related = [
        'estudiante__persona',
        'estudiante__plan',
        'proceso_matricula',
    ]

    list_filter = [
        'proceso_matricula',
        'estudiante__plan',
    ]

    search_fields = [
        'estudiante__persona__numero_documento',
        'estudiante__persona__nombres',
        'estudiante__persona__nombre_social',
        'estudiante__persona__apellido1'
    ]

    autocomplete_fields = ['estudiante']

    def documento(self, obj):
        return obj.estudiante.persona.documento()
    documento.admin_order_field = 'estudiante__persona__numero_documento'

    def ano(self, obj):
        return obj.proceso_matricula.ano
    ano.short_description = 'año'

    def nombre(self, obj):
        return obj.estudiante.persona.nombre_completo()

    def plan(self, obj):
        return obj.estudiante.plan
    plan.admin_order_field = 'estudiante__plan'


@admin.register(TNEEstudiante)
class TNEEstudianteAdmin(AdminRelacionEstudiante):
    list_display = [
        *AdminRelacionEstudiante.list_display,
        'paga_TNE',
        'orden_compra',
    ]

    list_filter = [*AdminRelacionEstudiante.list_filter, 'paga_TNE']


@admin.register(GratuidadEstudiante)
class GratuidadEstudianteAdmin(AdminRelacionEstudiante):
    list_display = [
        *AdminRelacionEstudiante.list_display,
        'tiene_gratuidad',
    ]

    list_filter = [*AdminRelacionEstudiante.list_filter, 'tiene_gratuidad']


@admin.register(EtapaEstudiante)
class EtapaEstudianteAdmin(AdminRelacionEstudiante):
    list_display = [
        *AdminRelacionEstudiante.list_display,
        'etapa_matricula',
        'creado',
    ]

    list_filter = [*AdminRelacionEstudiante.list_filter, 'etapa_matricula']


@admin.register(MatriculaEstudiante)
class MatriculaEstudianteAdmin(AdminRelacionEstudiante):
    list_display = [
        *AdminRelacionEstudiante.list_display,
        'beneficios_monto_total',
        'monto_final',
        'id_orden_compra',
        'estado',
        'pago',
    ]

    list_filter = [*AdminRelacionEstudiante.list_filter, 'estado']

    def id_orden_compra(self, obj):
        if obj.orden_compra:
            return obj.orden_compra.id

    def pago(self, obj):
        if obj.orden_compra:
            return obj.orden_compra.estado_pago == 1
    pago.boolean = True


@admin.register(ArancelEstudiante)
class ArancelEstudianteAdmin(AdminRelacionEstudiante):
    list_display = [
        *AdminRelacionEstudiante.list_display,
        'monto',
        'pago_cuotas',
        'id_orden_compra',
        'id_pagare',
        'estado',
    ]

    list_filter = [*AdminRelacionEstudiante.list_filter, 'pago_cuotas']

    def estado(self, obj):
        if obj.pagare:
            return obj.pagare.estado == 1
        elif obj.orden_compra:
            return obj.orden_compra.estado_pago == 1
    estado.boolean = True

    def id_orden_compra(self, obj):
        if obj.orden_compra:
            return obj.orden_compra.id

    def id_pagare(self, obj):
        if obj.pagare:
            return obj.pagare.id


@admin.register(EstudianteRespondeEncuesta)
class EstudianteRespondeEncuestaAdmin(AdminRelacionEstudiante):
    list_display = [
        *AdminRelacionEstudiante.list_display,
        'id_estudiante',
        'responde_encuesta',
        'estado',
        'modificado',
    ]

    list_filter = [
        *AdminRelacionEstudiante.list_filter,
        'responde_encuesta',
        'estudiante__estado_estudiante',
    ]

    def estado(self, obj):
        return obj.estudiante.estado_estudiante.nombre
    estado.admin_order_field = 'estudiante__estado_estudiante'

    def id_estudiante(self, obj):
        return obj.estudiante.id
    id_estudiante.admin_order_field = 'estudiante'


@admin.register(InhabilitantesMatricula)
class InhabilitantesMatriculaAdmin(AdminRelacionEstudiante):
    list_display = [
        *AdminRelacionEstudiante.list_display,
        'tiene_deuda_finanzas',
        'tiene_deuda_biblioteca',
        'modificado',
    ]

    list_filter = [
        *AdminRelacionEstudiante.list_filter,
        'tiene_deuda_finanzas',
        'tiene_deuda_biblioteca'
    ]

    actions = [
        'regularizar_deuda_finanzas',
        'regularizar_deuda_biblioteca',
    ]

    def regularizar_deuda_finanzas(self, request, queryset):
        queryset.filter(tiene_deuda_finanzas=True).update(
            tiene_deuda_finanzas=False, modificado=timezone.now())
    regularizar_deuda_finanzas.allowed_permissions = ('finanzas',)

    def has_finanzas_permission(self, request):
        return request.user.groups.filter(name='Encargade Finanzas').exists()

    def regularizar_deuda_biblioteca(self, request, queryset):
        queryset.filter(tiene_deuda_biblioteca=True).update(
            tiene_deuda_biblioteca=False, modificado=timezone.now())
    regularizar_deuda_biblioteca.allowed_permissions = ('biblioteca',)

    def has_biblioteca_permission(self, request):
        return request.user.groups.filter(name='Encargade Biblioteca').exists()


@admin.register(PostulanteEducacionContinua)
class PostulanteEducacionContinuaAdmin(PostulanteDefinitivoAdmin):
    list_display = [
        'nro_documento',
        'nombre',
        'plan',
        'habilitado',
        'resultado',
        'posicion_lista',
        'dcto_matricula',
        'dcto_arancel',
        'etapa',
        'regular',
    ]

    list_filter = [
        'proceso_matricula',
        'plan',
        'resultado_postulacion',
        FiltroEtapa,
    ]

    fieldsets = [
        (None, {
            'fields': ['persona', 'proceso_matricula', 'plan', 'habilitado']
        }),
        ('Datos ingreso', {
            'classes': ('collapse',),  # no mostrar por defecto
            'fields': [
                'resultado_postulacion', 'posicion_lista', 'clave',
                'tipo_descuento_matricula', 'monto_descuento_matricula',
                'descripcion_descuento_matricula', 'tipo_descuento_arancel',
                'monto_descuento_arancel', 'descripcion_descuento_arancel',
            ]
        }),
        ('Datos Matrícula', {
            'classes': ('collapse',),  # no mostrar por defecto
            'fields': [
                'acepta_vacante', 'estudiante', 'etapa', 'regular'
            ]
        }),
    ]

    def dcto_matricula(self, obj: PostulanteEducacionContinua):
        if obj.tipo_descuento_matricula == 0:
            return f'${obj.monto_descuento_matricula}'

        if obj.tipo_descuento_matricula == 1:
            return f'{obj.monto_descuento_matricula}%'

    def dcto_arancel(self, obj: PostulanteEducacionContinua):
        if obj.tipo_descuento_arancel == 0:
            return f'${obj.monto_descuento_arancel}'

        if obj.tipo_descuento_arancel == 1:
            return f'{obj.monto_descuento_arancel}%'
