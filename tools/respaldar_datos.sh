#!/bin/bash

python manage.py dumpdata \
    -e=admin.logentry -e=auth.permission -e=contenttypes -e=sessions \
    --indent=2 --verbosity=1 --natural-foreign \
    -o "tools/respaldo_$(date +'%Y-%m-%d_%H-%M').json"

read -n 1 -p "Presione cualquier tecla para terminar"
