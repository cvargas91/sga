#!/bin/bash

echo "copiando archivos en $1 al contenedor"
docker cp "$1/." "django:/home/app/web/datos_estudiantes"

docker exec django \
    python manage.py importar_estudiantes_antiguos datos_estudiantes

read -n 1 -p "Presione cualquier tecla para terminar"
