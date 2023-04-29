#!/bin/bash

python manage.py graph_models \
    matricula pagos \
    -X *Productos,Pago*,Bancos,DTE,OrdenCompraDetalle,ModeloRegistraFechas,Persona,Estudiante,Plan \
    -g --arrow-shape normal --hide-edge-labels \
    -o "tools/matricula_$(date +'%Y-%m-%d').png"

read -n 1 -p "Presione cualquier tecla para terminar"
