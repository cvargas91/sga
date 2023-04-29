#!/bin/bash

docker exec django \
    python manage.py loaddata \
    deptos_carreras_planes comunas periodos \
    datos_pagos etapas_matricula vias_ingreso proceso2021 modalidades_cuotas

read -n 1 -p "Presione cualquier tecla para terminar"
