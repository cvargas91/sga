#!/bin/bash

python manage.py graph_models \
    academica curso inscripcion persona auth -X AbstractUser,Permission -g \
    --arrow-shape normal --hide-edge-labels \
    -o "tools/models_$(date +'%Y-%m-%d').png"

read -n 1 -p "Presione cualquier tecla para terminar"
