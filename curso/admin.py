from django.contrib import admin

from .models import (
    CursosCompartidos, Periodo, Curso, DocenteCurso, AyudanteCurso, EstudianteCurso, Acta, Horario,
    Evaluacion, Nota, Modulo, EstadoEstudianteCurso, Actividad, CategoriaActividad
)

admin.site.register(Periodo)
admin.site.register(Curso)
admin.site.register(DocenteCurso)
admin.site.register(AyudanteCurso)
admin.site.register(EstadoEstudianteCurso)
admin.site.register(EstudianteCurso)
admin.site.register(Acta)
admin.site.register(Horario)
admin.site.register(Evaluacion)
admin.site.register(Nota)
admin.site.register(Modulo)
admin.site.register(CursosCompartidos)
admin.site.register(Actividad)
admin.site.register(CategoriaActividad)
