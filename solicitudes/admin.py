from django.contrib import admin
from .models import (Solicitud, TipoSolicitud, CausaSolicitud, SolicitudCambioCarrera,
                     SolicitudPostergacion, SolicitudReintegracion, SolicitudRenuncia,
                     PeriodoTipoSolicitud)
# Register your models here.

admin.site.register(Solicitud)
admin.site.register(TipoSolicitud)
admin.site.register(CausaSolicitud)
admin.site.register(PeriodoTipoSolicitud)
admin.site.register(SolicitudCambioCarrera)
admin.site.register(SolicitudPostergacion)
admin.site.register(SolicitudReintegracion)
admin.site.register(SolicitudRenuncia)
