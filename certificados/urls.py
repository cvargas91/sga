from django.urls import path, include
from certificados import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'solicitudes', views.SolicitudCertificadoViewset, basename='solicitudes')
router.register(r'certificados', views.CertificadoViewSet, basename='certificados')


urlpatterns = [
    path('', include(router.urls)),
    path('tipos-certificado/', views.TiposCertificadosView.as_view(), name='tipos-cert'),
    path('validar-certificado/', views.validar_certificado, name='validar-cert'),
    path('obtener-certificado/', views.obtener_certificado, name='obtener-cert'),
    path('anular-certificado/', views.anular_certificado, name='anular-cert'),
    path('enviar-solicitud/', views.enviar_solicitud, name='enviar-solicitud'),
    path('previsualizar-certificado-personalizado/', views.previsualizar_certificado_personalizado,
         name='previsualizar-certificado-personalizado'),
    path('resolver-solicitud/<int:pk>/', views.ResolucionSolicitudView.as_view()),
]
