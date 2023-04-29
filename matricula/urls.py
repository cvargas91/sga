from django.urls import include, path
from rest_framework import routers

from matricula.views.comunes import (
    PeriodoProcesoMatriculaView, get_detalle_periodo_actual, DatosContactoViewset,
    MatriculaEstudianteView, ArancelEstudianteView, aceptar_pagare, resumen,
    HistorialMatriculaEstudianteView, aceptar_contrato
)
from matricula.views.estudiantes_nuevos import (
    login_postulantes, validar_token_postulantes, aceptar_vacante,
)
from matricula.views.estudiantes_antiguos import (
    login_estudiantes_antiguos, validar_token_estudiantes_antiguos, InhabilitantesMatriculaView,
    comenzar_proceso_estudiante_antiguo,
)
from matricula.views.educacion_continua import (
    login_educacion_continua, validar_token_educacion_continua, aceptar_vacante_educacion_continua,
)

router = routers.DefaultRouter()
router.register('datos-contacto', DatosContactoViewset, 'datos-contacto')

urlpatterns = [
    path('', include(router.urls)),
    path('periodos-matricula/', PeriodoProcesoMatriculaView.as_view()),
    path('detalles-periodo-actual/', get_detalle_periodo_actual),

    path('login-postulantes/', login_postulantes),
    path('validar-token-postulantes/', validar_token_postulantes),
    path('aceptar-vacante/', aceptar_vacante),

    path('login-estudiantes-antiguos/', login_estudiantes_antiguos),
    path('validar-token-estudiantes-antiguos/', validar_token_estudiantes_antiguos),
    path('inhabilitantes-matricula/<int:estudiante_id>/', InhabilitantesMatriculaView.as_view()),
    path('comenzar-proceso-estudiante-antiguo/', comenzar_proceso_estudiante_antiguo),

    path('login-educacion-continua/', login_educacion_continua),
    path('validar-token-educacion-continua/', validar_token_educacion_continua),
    path('aceptar-vacante-educacion-continua/', aceptar_vacante_educacion_continua),

    path('matricula-estudiante/<int:estudiante_id>/', MatriculaEstudianteView.as_view()),
    path('arancel-estudiante/<int:estudiante_id>/', ArancelEstudianteView.as_view()),
    path('aceptar-pagare/', aceptar_pagare),
    path('aceptar-contrato/', aceptar_contrato),
    path('resumen/<int:estudiante_id>/', resumen),

    path(
        'historial-matricula-estudiante/<int:persona_id>/',
        HistorialMatriculaEstudianteView.as_view(),
    ),
]
