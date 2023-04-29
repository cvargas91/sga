from django.urls import include, path
from rest_framework import routers
from .views import (
    PeriodoViewSet, CursoViewSet, CursoResumenViewSet, CursoIntegrantesView, CursoHorarioView,
    HistorialCursosView, OpcionesCursoView, CategoriaActividadViewSet, CursosDocenteView,
    ActividadViewSet, ActividadesCursoViewSet, EvaluacionesActividadViewSet, EvaluacionViewSet,
    EvaluacionesCursoViewset, NotasEvaluacionViewset, TestNotaViewset, CursoEstudiantesView,
    NotasEstudianteCursoView, ConfiguracionCursoView, calcular_notas_presentacion,
    calcular_notas_finales, NotasExamenViewset, VistaResumenCursoView, notas_resumen_curso
)

router = routers.DefaultRouter()
router.register(r'periodos', PeriodoViewSet)
router.register(r'cursos', CursoViewSet)
router.register(r'cursos-resumen', CursoResumenViewSet)
router.register(r'categorias-actividad', CategoriaActividadViewSet)
router.register(r'actividades', ActividadViewSet)         # usado solo en desarrollo
router.register(r'evaluaciones', EvaluacionViewSet)
router.register(r'actividades-curso', ActividadesCursoViewSet)
router.register(r'evaluaciones-actividad', EvaluacionesActividadViewSet)
router.register(r'evaluaciones-curso', EvaluacionesCursoViewset)
router.register(r'notas', NotasEvaluacionViewset)
router.register(r'test-notas', TestNotaViewset)
router.register(r'notas-examen', NotasExamenViewset)
router.register(r'curso-resumen', VistaResumenCursoView)

urlpatterns = [
    path('', include(router.urls)),
    path('historial-cursos/', HistorialCursosView.as_view()),
    path('opciones-curso/', OpcionesCursoView.as_view()),
    path('curso-integrantes/<int:pk>/', CursoIntegrantesView.as_view()),
    path('curso-horario/<int:pk>/', CursoHorarioView.as_view()),
    path('cursos-docente/', CursosDocenteView.as_view()),
    path('curso-estudiantes/', CursoEstudiantesView.as_view()),
    path('notas-curso/', NotasEstudianteCursoView.as_view()),
    path('programa-curso/<int:pk>', ConfiguracionCursoView.as_view()),
    path('notas-presentacion-curso/', calcular_notas_presentacion),
    path('notas-finales-curso/', calcular_notas_finales),
    path('resumen-curso/<int:curso>', notas_resumen_curso),
    # path('notas-examen/<int:pk>', .as_view()),

]
