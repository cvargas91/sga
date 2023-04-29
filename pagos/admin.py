""" Admin pagos """

# django
from django.contrib import admin, messages
from django.contrib.auth.decorators import permission_required
from django.db.models import F
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe
from django.views import View

# django history
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, CHANGE

from .forms import OrdenCompraForm

# Models
from matricula.models import MatriculaEstudiante

from .models import (
    CategoriasProductos, SubCategoriasProductos, Productos, ModalidadPago, FormaPago, OrdenCompra,
    OrdenCompraDetalle, PagoWebPay,
)


class FiltroProductos(admin.SimpleListFilter):
    title = 'subcategoría de producto'
    parameter_name = 'producto'

    def lookups(self, request, model_admin):
        return (
            (1, 'Matricula'),
            (2, 'TNE'),
            (3, 'Arancel'),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        # buscar todas las compras detalle que compraron un producto de la subcategoría
        compra_detalles = OrdenCompraDetalle.objects.filter(
            producto__in=Productos.objects.filter(subcategoria=self.value())
        )

        # filtrar ordenes
        ordenes_ids = compra_detalles.values_list('orden_compra')
        return queryset.filter(id__in=ordenes_ids)


class FiltroMonto(admin.SimpleListFilter):
    title = 'monto'
    parameter_name = 'monto'

    def lookups(self, request, model_admin):
        return (
            (1, 'monto 0'),
            (2, 'monto mayor a 0'),
        )

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        monto = int(self.value())

        if monto == 1:
            return queryset.filter(monto_total=F("total_descuento_beneficios"))

        return queryset.exclude(monto_total=F("total_descuento_beneficios"))


class FiltroAno(admin.SimpleListFilter):
    title = 'año'
    parameter_name = 'ano'

    def lookups(self, request, model_admin):
        return [(categoria.id, categoria.nombre) for categoria in CategoriasProductos.objects.all()]

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset

        # buscar todas las compras detalle que compraron un producto de la subcategoría
        compra_detalles = OrdenCompraDetalle.objects.filter(
            producto__in=Productos.objects.filter(categoria=self.value())
        )

        # filtrar ordenes
        ordenes_ids = compra_detalles.values_list('orden_compra')
        return queryset.filter(id__in=ordenes_ids)


@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    # vista de lista
    list_display = [
        'id',
        'documento',
        'nombre_legal',
        'forma_pago',
        'monto',
        'estado_pago',
        'productos',
        'folio_dte',
        'creado',
        'fecha_pago',
    ]

    def get_list_display(self, request):
        if request.user.has_perm('pagos.recibir_pagos'):
            return self.list_display + ['validar_pago']

        return self.list_display

    list_select_related = [
        'persona',
    ]

    list_filter = [
        FiltroAno,
        'estado_pago',
        'forma_pago',
        FiltroProductos,
        FiltroMonto,
    ]

    search_fields = [
        'persona__numero_documento',
        'persona__nombres',
        'persona__nombre_social',
        'persona__apellido1',
    ]

    # cambios al formulario
    def get_fields(self, request, obj):
        if request.user.is_superuser:
            return super().get_fields(request, obj)

        # usuarios sin permiso global solo ven información general
        return [
            'id',
            'nombre_legal',
            'monto',
            'forma_pago',
            'estado',
            'estado_pago',
            'fecha_pago',
            'folio_dte',
            'comentario',
        ]

    def get_readonly_fields(self, request, obj):
        if request.user.is_superuser:
            return []

        # usuarios sin permiso global no pueden editar datos críticos
        return [
            'id',
            'nombre_legal',
            'monto',
            'forma_pago',
            'estado',
            'estado_pago',
            'fecha_pago',
        ]

    # campos calculados
    def documento(self, obj):
        return obj.persona.documento()
    documento.admin_order_field = 'persona__numero_documento'

    def nombre_legal(self, obj):
        return obj.persona.nombre_legal()

    def monto(self, obj):
        return f'${obj.monto_a_pagar()}'

    def productos(self, obj):
        return list(
            OrdenCompraDetalle.objects.filter(orden_compra=obj)
            .values_list('producto__nombre', flat=True)
        )

    # link para validar pago
    def validar_pago(self, obj):
        if obj.estado_pago == 0:
            return mark_safe(
                f'<a href="{reverse("admin:recepcion-pagos", args=[obj.id])}">validar pago</a>'
            )
    validar_pago.short_description = 'acciones'

    # url custom
    def get_urls(self):
        urls_nuevas = [
            path('recepcion_pago/<int:orden_id>/', RecepcionPago.as_view(), name='recepcion-pagos'),
        ]

        return urls_nuevas + super().get_urls()


@method_decorator([
    permission_required('pagos.recibir_pagos'),
    admin.site.admin_view,
], name='dispatch')
class RecepcionPago(View):
    form = OrdenCompraForm

    def get_context(self, request, orden_compra, form):
        titulo = 'Recepción de Pagos'

        # acotar opciones a solo formas de pago presenciales
        form.fields['forma_pago'].queryset = FormaPago.objects.filter(id__in=(2, 3, 4, 5, 6))

        return dict(
            admin.site.each_context(request),  # contexto común a todo el django admin
            opts=OrdenCompra._meta,  # contexto para el breadcrumbs
            has_view_permission=request.user.has_perm('pagos.view_ordencompra'),
            title=titulo,
            original=titulo,
            orden_compra=orden_compra,
            form=form,
            form_url=reverse('admin:recepcion-pagos', args=[orden_compra.id]),
        )

    def template(self, request, orden_compra, form):
        return TemplateResponse(
            request,
            'recepcion_pago.html',
            self.get_context(request, orden_compra, form)
        )

    def get(self, request, orden_id):
        orden_compra = get_object_or_404(OrdenCompra, id=orden_id)

        # chequear que se puede validar esta orden de compra
        if orden_compra.estado_pago != 0:
            messages.add_message(
                request,
                messages.ERROR,
                'Solo se pueden validar ordenes de compra en estado pendiente.',
            )
            return HttpResponseRedirect(reverse('admin:pagos_ordencompra_changelist'))

        form = self.form(instance=orden_compra)
        return self.template(request, orden_compra, form)

    def post(self, request, orden_id):
        orden_compra = get_object_or_404(OrdenCompra, id=orden_id)

        # chequear que se puede validar esta orden de compra
        if orden_compra.estado_pago != 0:
            messages.add_message(
                request,
                messages.ERROR,
                'Solo se pueden validar ordenes de compra en estado pendiente.',
            )
            return HttpResponseRedirect(reverse('admin:pagos_ordencompra_changelist'))

        form = self.form(request.POST)
        if form.is_valid():

            # detectar ordenes de compra de matrícula
            if OrdenCompraDetalle.objects.filter(
                orden_compra=orden_compra,
                producto__nombre__icontains='matrícula'
            ).exists():

                # chequear que exista una matrícula asociada
                try:
                    matricula = MatriculaEstudiante.objects.get(orden_compra=orden_compra)
                except MatriculaEstudiante.DoesNotExist:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        f'No existe una matricula asociada a la orden de compra.',
                    )
                    return self.template(request, orden_compra, form)

                # marcar matrícula válida
                matricula.validar()

            # actualizar estado orden de compra
            orden_compra.validar()

            # recuperar datos del formulario
            orden_compra.folio_dte = form['folio_dte'].data
            orden_compra.comentario = form['comentario'].data
            orden_compra.forma_pago = FormaPago.objects.get(id=form['forma_pago'].data)
            orden_compra.save()

            # registrar acción
            LogEntry.objects.log_action(
                user_id=request.user.id,
                action_flag=CHANGE,
                content_type_id=ContentType.objects.get_for_model(orden_compra).id,
                object_id=orden_compra.id,
                object_repr=str(orden_compra),
                change_message='Validó este pago.',
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                f'Se ha validado la orden de compra {orden_compra}.',
            )
            # TODO: agregar segundo paso para registrar datos específicos de forma de pago
            return HttpResponseRedirect(reverse('admin:pagos_ordencompra_changelist'))

        return self.template(request, orden_compra, form)


# Register your models here.
admin.site.register(CategoriasProductos)
admin.site.register(SubCategoriasProductos)
admin.site.register(Productos)
admin.site.register(ModalidadPago)
admin.site.register(FormaPago)
admin.site.register(OrdenCompraDetalle)
admin.site.register(PagoWebPay)
