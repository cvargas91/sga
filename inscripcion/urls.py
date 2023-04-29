from django.urls import include, path
from rest_framework import routers
from .views import (
    ProcesoInscripcionViewset, EnvioInscripcionViewset,
    CursosInscribiblesView, SolicitudCursoViewset
)

router = routers.DefaultRouter()
router.register(r'procesos', ProcesoInscripcionViewset)
router.register(r'envios', EnvioInscripcionViewset)
router.register(r'previsualizar-inscripcion', SolicitudCursoViewset)


urlpatterns = [
    path('', include(router.urls)),
    path('cursos/', CursosInscribiblesView.as_view()),
]
