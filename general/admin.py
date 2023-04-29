from django.contrib import admin

from .models import (
    Region, Comuna, Pais, Sede, Espacio,
)

admin.site.register(Region)
admin.site.register(Comuna)
admin.site.register(Pais)
admin.site.register(Sede)
admin.site.register(Espacio)
