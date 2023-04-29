from django.urls import include, path
from rest_framework import routers
from .views import (
    PersonaViewSet, MonitoreoEstudiantesView, OpcionesMonitoreoView, PerfilView, login_google,
    validar_token, FotoPerfilView, GroupView, PersonaRolView, HistorialEstadoEstudianteView,
    EstudianteViewSet, ResumenAcademicoView, login_jwt
)

router = routers.DefaultRouter()
router.register(r'personas', PersonaViewSet)
router.register(r'estudiantes', EstudianteViewSet)
router.register(r'monitoreo-estudiantes', MonitoreoEstudiantesView)

urlpatterns = [
    path('', include(router.urls)),
    path('login-google/', login_google),
    path('login-jwt/', login_jwt),
    path('validar-token/', validar_token),
    path('monitoreo-opciones/', OpcionesMonitoreoView.as_view()),
    path('perfil/<int:pk>/', PerfilView.as_view()),
    path('foto-perfil/<int:pk>/', FotoPerfilView.as_view()),
    path('historial-estado-estudiante/<int:pk>/', HistorialEstadoEstudianteView.as_view()),
    path('grupos/', GroupView.as_view()),
    path('personas-rol/', PersonaRolView.as_view()),
    path('resumen-academico/<int:pk>/', ResumenAcademicoView.as_view()),
]
