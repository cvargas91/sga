from rest_framework.generics import ListAPIView

from persona.permisos import TodosSoloLeer

from .models import (
    ModalidadCuotaPagare
)
from .serializers import (
    ModalidadCuotaPagareSerializer
)


class ModalidadCuotaPagareView(ListAPIView):
    queryset = ModalidadCuotaPagare.objects.all()
    serializer_class = ModalidadCuotaPagareSerializer
    permission_classes = [TodosSoloLeer, ]

    def get_queryset(self):
        queryset = super().get_queryset().filter(proceso_matricula__activo=True)

        plan = self.request.query_params.get('plan', None)
        if plan is not None:
            queryset = queryset.filter(plan__id=plan)

        curso = self.request.query_params.get('curso', None)
        if curso is not None:
            queryset = queryset.filter(curso_asociado=curso)

        return queryset
