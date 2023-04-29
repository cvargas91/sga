from rest_framework import mixins
from rest_framework import viewsets

from persona.permisos import TodosSoloLeer

from .models import (
    Region, Comuna, Pais,
)
from .serializers import (
    RegionSerializer, ComunaSerializer, PaisSerializer,
)


class RegionViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [TodosSoloLeer, ]


class ComunaViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Comuna.objects.all()
    serializer_class = ComunaSerializer
    permission_classes = [TodosSoloLeer, ]


class PaisViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Pais.objects.all()
    serializer_class = PaisSerializer
    permission_classes = [TodosSoloLeer, ]
