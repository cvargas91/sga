from django.urls import include, path
from rest_framework import routers
from.views import ModalidadCuotaPagareView

router = routers.DefaultRouter()

urlpatterns = [
    path('modalidades-cuotas/', ModalidadCuotaPagareView.as_view()),
    path('', include(router.urls)),
]
