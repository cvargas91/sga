from django.contrib import admin

from .models import ProcesoInscripcion, EnvioInscripcion, SolicitudCurso

admin.site.register(ProcesoInscripcion)
admin.site.register(EnvioInscripcion)
admin.site.register(SolicitudCurso)
