from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from matricula.models import (
    ProcesoMatricula, EtapaEstudiante, MatriculaEstudiante, GratuidadEstudiante,
)

from .models import (
    Persona, Estudiante, EstadoEstudiante, HistorialEstadoEstudiante,
)
from .forms import AgregarPersonaForm


# modificar textos del sitio admin
titulo = 'Admin UAysén'
if settings.DEBUG:
    titulo = f'(PRUEBA) Admin UAysén'

admin.site.site_header = titulo
admin.site.site_title = titulo
admin.site.index_title = 'Índice'


class PersonaInline(admin.StackedInline):
    model = Persona

    # no mostar formulario de persona si es que no existe aún
    def get_extra(self, request, obj=None, **kwargs):
        return 0


class CustomUserAdmin(UserAdmin):
    list_display = [
        'username',
        'documento',
        'nombre',
        'mail_institucional',
        'is_staff',
        'grupos',
    ]
    search_fields = [
        'persona__numero_documento',
        'persona__nombres',
        'persona__nombre_social',
        'persona__apellido1'
    ]

    fieldsets = [
        (None, {
            'fields': ('username', 'password'),
        }),
        ('Permissions', {
            'fields': (('is_active', 'is_staff', 'is_superuser'), 'groups'),
        }),
    ]
    inlines = [
        PersonaInline,
    ]

    def documento(self, obj):
        return obj.persona.documento()
    documento.admin_order_field = 'persona__numero_documento'

    def nombre(self, obj):
        return obj.persona.nombre_legal()
    nombre.admin_order_field = 'persona__apellido1'

    def mail_institucional(self, obj):
        return obj.persona.mail_institucional
    mail_institucional.admin_order_field = 'persona__mail_institucional'

    def grupos(self, obj):
        return ', '.join([group.name for group in obj.groups.all()])


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    list_display = [
        'documento',
        'nombre_completo',
        'mail_institucional',
    ]

    search_fields = [
        'numero_documento',
        'nombres',
        'nombre_social',
        'apellido1'
    ]

    exclude = [
        'user'
    ]

    def get_form(self, request, obj=None, **kwargs):
        if not request.user.is_superuser and obj is None:
            return AgregarPersonaForm
        return super().get_form(request, obj, **kwargs)

    def dv(self, obj):
        return obj.digito_verificador


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
        return queryset.filter(id__in=ids_estudiantes)


class FiltroCurso(admin.SimpleListFilter):
    title = 'curso'
    parameter_name = 'curso'

    def lookups(self, request, model_admin):
        return (
            (1, 'primer año'),
            (2, 'curso superior'),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        curso = int(self.value())

        ingreso_primer_año = ProcesoMatricula.objects.get(activo=True).periodo_ingreso

        if curso == 1:
            return queryset.filter(periodo_ingreso=ingreso_primer_año)

        return queryset.exclude(periodo_ingreso=ingreso_primer_año)


class FiltroEstadoMatricula(admin.SimpleListFilter):
    title = 'estado matricula'
    parameter_name = 'matricula'

    def lookups(self, request, model_admin):
        return MatriculaEstudiante.estados

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        estado = int(self.value())

        ids_estudiantes = MatriculaEstudiante.objects.filter(
            proceso_matricula=ProcesoMatricula.objects.get(activo=True),
            estado=estado,
        ).values_list('estudiante')

        return queryset.filter(id__in=ids_estudiantes)


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = [
        'documento',
        'nombre',
        'plan',
        'estado_estudiante',
        'periodo_ingreso',
        'etapa',
        'gratuidad',
        'estado_mat',
        'pago_mat',
    ]

    list_filter = [
        FiltroEtapa,
        FiltroCurso,
        FiltroEstadoMatricula,
        'plan',
        'estado_estudiante',
        'periodo_ingreso',
    ]

    search_fields = [
        'persona__numero_documento',
        'persona__nombres',
        'persona__nombre_social',
        'persona__apellido1'
    ]

    readonly_fields = [
        'documento',
        'mail_institucional',
        'etapa',
        'gratuidad',
        'estado_mat',
        'pago_mat',
    ]

    def documento(self, obj):
        return obj.persona.documento()
    documento.admin_order_field = 'persona__numero_documento'

    def nombre(self, obj):
        return obj.persona.nombre_legal()

    def mail_institucional(self, obj):
        return obj.persona.mail_institucional

    def etapa(self, obj):
        return obj.etapa_estudiante()

    def estado_mat(self, obj):
        try:
            matricula = MatriculaEstudiante.objects.get(
                proceso_matricula=ProcesoMatricula.objects.get(activo=True),
                estudiante=obj,
            )
            return matricula.get_estado_display()

        except MatriculaEstudiante.DoesNotExist:
            pass

    def pago_mat(self, obj):
        try:
            matricula = MatriculaEstudiante.objects.get(
                proceso_matricula=ProcesoMatricula.objects.get(activo=True),
                estudiante=obj,
            )
            if matricula.orden_compra:
                return matricula.orden_compra.estado_pago == 1

        except MatriculaEstudiante.DoesNotExist:
            pass
    pago_mat.boolean = True

    def gratuidad(self, obj):
        try:
            gratuidad = GratuidadEstudiante.objects.get(
                proceso_matricula=ProcesoMatricula.objects.get(activo=True),
                estudiante=obj,
            )
            return gratuidad.tiene_gratuidad

        except GratuidadEstudiante.DoesNotExist:
            pass
    gratuidad.boolean = True


admin.site.register(EstadoEstudiante)
admin.site.register(HistorialEstadoEstudiante)
