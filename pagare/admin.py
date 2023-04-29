from django.contrib import admin, messages
from django.contrib.auth.decorators import permission_required
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

from .models import ModalidadCuotaPagare, Pagare
from .forms import PagareForm

admin.site.register(ModalidadCuotaPagare)


@admin.register(Pagare)
class PagareAdmin(admin.ModelAdmin):
    list_display = [
        'documento',
        'ano',
        'nombre',
        'cantidad_cuotas',
        'plan',
        'estado',
        'creado',
        'validado_por',
        'validado_fecha',
        'recibir_pagare',
    ]

    list_select_related = [
        'arancel_estudiante__estudiante__persona',
        'arancel_estudiante__estudiante__plan',
        'arancel_estudiante__proceso_matricula',
    ]

    list_filter = [
        'arancel_estudiante__proceso_matricula',
        'estado',
        'arancel_estudiante__estudiante__plan',
    ]

    search_fields = [
        'arancel_estudiante__estudiante__persona__numero_documento',
        'arancel_estudiante__estudiante__persona__nombres',
        'arancel_estudiante__estudiante__persona__apellido1',
        'arancel_estudiante__estudiante__persona__nombre_social',
    ]

    # cambios al formulario
    def get_fields(self, request, obj):
        if request.user.is_superuser:
            return super().get_fields(request, obj)

        # usuarios sin permiso global solo ven información general
        return [
            *self.list_display,
            'documento_escaneado',
        ]

    def get_readonly_fields(self, request, obj):
        if request.user.is_superuser:
            return []

        # usuarios sin permiso global no pueden editar datos críticos
        return [
            *self.list_display,
        ]

    def documento(self, obj):
        return obj.arancel_estudiante.estudiante.persona.numero_documento
    documento.admin_order_field = 'arancel_estudiante__estudiante__persona__numero_documento'

    def ano(self, obj):
        return obj.arancel_estudiante.proceso_matricula.ano
    ano.short_description = 'año'

    def nombre(self, obj):
        return obj.arancel_estudiante.estudiante.persona.nombre_legal()

    def plan(self, obj):
        return obj.arancel_estudiante.estudiante.plan
    plan.admin_order_field = 'arancel_estudiante__estudiante__plan'

    actions = ['marcar_como_recibido']

    def marcar_como_recibido(self, request, queryset):
        queryset = queryset.filter(validado=False)
        for pagare in queryset:
            pagare.recibir_pagare(request)
        return

    marcar_como_recibido.allowed_permissions = ('view',)

    # vista custom para recibir pagare
    def recibir_pagare(self, obj):
        if obj.estado == 0 and not obj.validado:
            return mark_safe(
                f'<a href="{reverse("admin:recepcion-pagare", args=[obj.id])}">recibir pagare</a>'
            )
    recibir_pagare.short_description = 'acciones'

    # url custom
    def get_urls(self):
        urls_nuevas = [
            path(
                'recepcion_pagare/<int:pagare_id>/',
                RecepcionPagare.as_view(),
                name='recepcion-pagare'
            ),
        ]

        return urls_nuevas + super().get_urls()


@method_decorator([
    permission_required('pagare.recibir_pagare'),
    admin.site.admin_view,
], name='dispatch')
class RecepcionPagare(View):
    form = PagareForm

    def get_context(self, request, pagare, form):
        titulo = 'Recepción de Pagaré'

        return dict(
            admin.site.each_context(request),  # contexto común a todo el django admin
            opts=Pagare._meta,  # contexto para el breadcrumbs
            has_view_permission=request.user.has_perm('pagare.view_pagare'),
            title=titulo,
            original=titulo,
            pagare=pagare,
            form=form,
            form_url=reverse('admin:recepcion-pagare', args=[pagare.id]),
        )

    def template(self, request, pagare, form):
        return TemplateResponse(
            request,
            'recepcion_pagare.html',
            self.get_context(request, pagare, form)
        )

    def get(self, request, pagare_id):
        pagare = get_object_or_404(Pagare, id=pagare_id)

        # chequear que se puede recibir el pagaré
        if pagare.estado != 0 or pagare.validado:
            messages.add_message(
                request,
                messages.ERROR,
                'Solo se pueden recibir pagarés en estado pendiente.',
            )
            return HttpResponseRedirect(reverse('admin:pagare_pagare_changelist'))

        form = self.form(instance=pagare)
        return self.template(request, pagare, form)

    def post(self, request, pagare_id):
        pagare = get_object_or_404(Pagare, id=pagare_id)

        # chequear que se puede recibir el pagaré
        if pagare.estado != 0 or pagare.validado:
            messages.add_message(
                request,
                messages.ERROR,
                'Solo se pueden recibir pagarés en estado pendiente.',
            )
            return HttpResponseRedirect(reverse('admin:pagare_pagare_changelist'))

        form = self.form(request.POST, request.FILES)
        if form.is_valid():
            # actualizar estado pagaré
            pagare.recibir_pagare(request)

            # recuperar datos del formulario
            pagare.documento_escaneado = request.FILES['documento_escaneado']
            pagare.save()

            # registrar acción
            LogEntry.objects.log_action(
                user_id=request.user.id,
                action_flag=CHANGE,
                content_type_id=ContentType.objects.get_for_model(pagare).id,
                object_id=pagare.id,
                object_repr=str(pagare),
                change_message='Recepcionó este pagaré.',
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                f'Se ha validado el pagaré {pagare}.',
            )
            return HttpResponseRedirect(reverse('admin:pagare_pagare_changelist'))

        return self.template(request, pagare, form)
