#!/bin/bash

echo "copiando archivo $1 al contenedor"
docker cp $1 django:/home/app/web/respaldo.json

echo "importando datos"
docker exec django python manage.py loaddata respaldo.json

read -n 1 -p "Presione cualquier tecla para terminar"
