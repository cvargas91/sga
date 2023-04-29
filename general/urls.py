from django.urls import include, path
from rest_framework import routers

from .views import (
    RegionViewset, ComunaViewset, PaisViewset,
)

router = routers.DefaultRouter()
router.register(r'regiones', RegionViewset)
router.register(r'comunas', ComunaViewset)
router.register(r'paises', PaisViewset)

urlpatterns = [
    path('', include(router.urls)),
]
