from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms import ValidationError
from rest_framework import serializers

# TODO: Considerar posibles cambios de escalas de evaluación en el reglamento

mensaje_ponderacion = "La ponderación de la evaluación debe ser entre 1 y 100"
validadores_ponderaciones = [
    MinValueValidator(1, message=mensaje_ponderacion),
    MaxValueValidator(100, message=mensaje_ponderacion)
    ]


def validatar_nota(nota):
    if nota < 1.0 or nota > 7.0:
        raise ValidationError(
            ('La nota de la evaluación debe ser entre 1.0 y 7.0'))


def validar_suma_ponderaciones(data, modelo):  # modelos validos:
    modelo_data = data.get(modelo)             # strings "actividades" o "evaluaciones"
    ponderacion_total = 0

    for modelo in modelo_data:
        ponderacion_total += modelo['ponderacion']

    if ponderacion_total != 100:
        raise serializers.ValidationError({
            'detail': 'Las ponderaciones del listado deben sumar 100'})
    return data
