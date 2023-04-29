from django.urls import path, include
from solicitudes import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'causas-solicitudes', views.CausaSolicitudViewSet)
router.register(r'periodos-solicitudes', views.PeriodoTipoSolicitudViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('tipos-solicitudes/', views.TipoSolicitudView.as_view()),
    path('estados-solicitudes/', views.EstadoSolicitudView.as_view()),
    path('solicitudes/', views.SolicitudView.as_view()),
    path('solicitudes/<int:pk>/', views.SolicitudDetalleView.as_view()),
    path('enviar-solicitud/', views.enviar_solicitud),
    path('resolver-solicitud/<int:pk>/', views.ResolucionSolicitudView.as_view()),
    path('actualizar-solicitud/<int:pk>/', views.DecretoResolucionSolicitudView.as_view()),
]
