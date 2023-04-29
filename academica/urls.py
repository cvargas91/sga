from django.urls import include, path
from rest_framework import routers
from .views import (
    DepartamentoViewSet, CarreraViewSet, PlanViewSet, MallaPlanViewSet, RamoViewSet,
    ConjuntoRamosViewSet, TiposCarrerasView, TiposFormacionView,
)

router = routers.DefaultRouter()
router.register(r'departamentos', DepartamentoViewSet)
router.register(r'carreras', CarreraViewSet)
router.register(r'planes', PlanViewSet)
router.register(r'mallas-planes', MallaPlanViewSet)
router.register(r'ramos', RamoViewSet)
router.register(r'conjuntos-ramos', ConjuntoRamosViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('tipos-carreras/', TiposCarrerasView.as_view()),
    path('tipos-formacion/', TiposFormacionView.as_view()),
]
