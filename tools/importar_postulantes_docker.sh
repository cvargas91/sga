#!/bin/bash

echo "copiando archivos en $1 al contenedor"
docker cp "$1/." "django:/home/app/web/datos_postulantes"

docker exec django \
    python manage.py importar_postulantes datos_postulantes $2

read -n 1 -p "Presione cualquier tecla para terminar"
