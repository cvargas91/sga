from django.urls import path

from .views import (
    pago_matricula, resultado_pago_matricula, estado_pago_matricula,
    pago_arancel, resultado_pago_arancel, estado_pago_arancel,
)


urlpatterns = [
    path('pago-matricula/', pago_matricula),
    path('resultado-pago-matricula/', resultado_pago_matricula, name='resultado-pago-matricula'),
    path('estado-pago-matricula/<int:estudiante_id>/', estado_pago_matricula),
    path('pago-arancel/', pago_arancel),
    path('resultado-pago-arancel/', resultado_pago_arancel, name='resultado-pago-arancel'),
    path('estado-pago-arancel/<int:estudiante_id>/', estado_pago_arancel),
]
