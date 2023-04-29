from django.contrib import admin

from .models import Departamento, Carrera, Plan, Ramo, MallaElectiva, MallaObligatoria, ConjuntoRamos, Requisito

admin.site.register(Departamento)
admin.site.register(Carrera)
admin.site.register(Plan)
admin.site.register(Ramo)
admin.site.register(MallaObligatoria)
admin.site.register(MallaElectiva)
admin.site.register(ConjuntoRamos)
admin.site.register(Requisito)
