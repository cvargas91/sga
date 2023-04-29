from django.urls import path
from .views import PersonaUcampusView, MatriculaUcampusView, MatriculaHistoricaUcampusView


urlpatterns = [
    path('personas/', PersonaUcampusView.as_view()),
    path('matriculas/', MatriculaUcampusView.as_view()),
    path('matriculas-historicas/', MatriculaHistoricaUcampusView.as_view()),
]
