from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.contrib.auth.decorators import login_required
# eliminar en produccion
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('api/schema/', login_required(SpectacularAPIView.as_view()), name='schema'),
    path('api/schema/swagger-ui/', login_required(
        SpectacularSwaggerView.as_view(url_name='schema')), name='swagger-ui'),
    path('api/schema/redoc/',
         login_required(SpectacularRedocView.as_view(url_name='schema')), name='redoc'),
    path('admin/', admin.site.urls),
    path('info-academica/', include('academica.urls')),
    path('certificados/', include('certificados.urls')),
    path('curso/', include('curso.urls')),
    path('general/', include('general.urls')),
    path('inscripcion/', include('inscripcion.urls')),
    path('matricula/', include('matricula.urls')),
    path('pagare/', include('pagare.urls')),
    path('pagos/', include('pagos.urls')),
    path('persona/', include('persona.urls')),
    path('ucampus/', include('ucampus.urls')),
    path('solicitudes/', include('solicitudes.urls')),
]

# servir archivos de media en servidor de desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
