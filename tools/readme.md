# Uso de Herramientas de Desarrollo

En el siguiente readme se explica cómo utilizar el comando para graficar modelos de django `graph_models`.


## Instalación

Para graficar el diagrama es necesario instalar Graphviz primero. Este paso presenta problemas en Windows, por lo que se entregaran instrucciones detalladas de acuerdo a lo encontrado en la documentación de [pygraphviz](https://pygraphviz.github.io/documentation/stable/install.html).

### Windows
Instalar manualmente la versión 2.46.0 para windows 10 (64 bits): [stable_windows_10_cmake_Release_x64_graphviz-install-2.46.0-win64.exe](https://gitlab.com/graphviz/graphviz/-/package_files/6164164/download)

\* puede ser necesario instalar [visual C/C++](https://visualstudio.microsoft.com/visual-cpp-build-tools/) para poder compilar la librería

Asegurarse de que se hayan agregado al PATH las librerías include y lib de graphviz (`C:\Program Files\Graphviz\include` y `C:\Program Files\Graphviz\lib` o similar respectivamente)

instalar **pydotplus**, esta librería tiende a ser más estable que pygraphviz
```
$ pip install pydotplus
```

### Linux
Instalar Graphviz utilizando el gestor de paquetes del sistema, algunos ejemplos son:
```
$ sudo apt-get install graphviz graphviz-dev  # Ubuntu/Debian
$ port install graphviz  # Fedora/Red Hat
$ pip install pydotplus
```

### Mac
instalar Graphviz utilizando Homebrew o MacPorts
```
$ brew install graphviz  # Homebrew
$ sudo apt-get install graphviz graphviz-dev  # MacPorts
$ pip install pydotplus
```


## Uso

para invocar la herramienta se utiliza el siguiente comando:
```
python manage.py graph_models [options] [app_label ...]
```

para graficar todos los modelos del sistema utilizar
```
python manage.py graph_models -a
```

y para graficar una app específica utilizar
```
python manage.py graph_models academica
```

### Scripts creados

actualmente existen 2 scripts para generar gráficos predeterminados:
- `tools/graficar_modelos.sh` diagrama los modelos académicos (academica, curso, inscripcion, persona).
- `tools/graficar_modelos_matricula.sh` diagrama los modelos de matrícula y pagos.


## Configuración

Existen muchas opciones distintas las cuales se pueden consultar utilizando el comando
```
python manage.py graph_models -h
```

A continuación se enumeran algunas de las que se consideran más útiles para este proyecto:
```
--disable-fields, -d
    No mostrar los campos de cada clase, solo los nombres de los modelos y sus relaciones

--group-models, -g
    Agrupar los modelos según aplicación
    se recomienda utilizar esta opción siempre que se grafique más de una app.

--all-applications, -a
    Incluir todas las aplicaciones que se encuentren en INSTALLED_APPS

--output OUTPUTFILE, -o OUTPUTFILE
    archivo de salido para el comando. El tipo del output es inferido del tipo del archivo
    especificado. Utilizar .png o .jpg para generar imágenes.

--exclude-columns EXCLUDE_COLUMNS, -x EXCLUDE_COLUMNS
    Esconder ciertos campos específicos del diagrama. También se puede cargar la lista desde un archivo.

--exclude-models EXCLUDE_MODELS, -X EXCLUDE_MODELS
    Excluir ciertos modelos del gráfico. También se puede cargar la lista desde un archivo.
    Se pueden utilizar comodines (*) en los nombres.

--include-models INCLUDE_MODELS, -I INCLUDE_MODELS
    Incluir solo ciertos modelos del pozo actual, se recomienda utilizar la opción -a.
    Se pueden utilizar comodines (*) en los nombres.

--disable-sort-fields, -S
    No ordenar los campos en orden alfabético. Por defecto se ordenan.

--hide-edge-labels
    Esconder los nombres de las relaciones en el gráfico. Puede ayudar a "limpiar" diagramas
    demasiado grandes

--arrow-shape {box,crow,curve,icurve,diamond,dot,inv,none,normal,tee,vee}
    Cambiar la forma de las flechas en el gráfico. Por defecto se usa dot.

--rankdir {TB,BT,LR,RL}
    Definir una dirección del gráfico, top-bottom, bottom-top, left-right, right-left.
    Por defecto se usa TB.
```


## Ejemplos

A continuación se muestran algunos ejemplos de configuraciones utilizadas para graficar aplicaciones específicas

- graficar modelos de app persona eliminando campos no esenciales
```
python manage.py graph_models `
    --arrow-shape normal --hide-edge-labels --rankdir BT -S -X AbstractUser,Permission,Pais,Comuna `
    -o "tools/modelos_persona.png" persona `
    -x genero,nombre_social,foto,biografia,mail_secundario,telefono_fijo,telefono_celular,nacionalidad,ciudad_origen,direccion_calle,direccion_numero,direccion_block,direccion_depto,direccion_villa,direccion_comuna,direccion_coyhaique,emergencia_nombre,emergencia_parentezco,emergencia_telefono_fijo,emergencia_telefono_laboral,emergencia_telefono_celular,emergencia_mail,educontinua_cargo,educontinua_empresa,educontinua_mail_laboral,autoriza_uso_imagen
```

- graficar modelos de app academica
```
python manage.py graph_models `
    --arrow-shape normal --hide-edge-labels --rankdir BT -S -X Malla `
    -o "tools/modelos_academica.png" academica
```

- graficar modelos de app curso
```
python manage.py graph_models `
    --arrow-shape normal --hide-edge-labels --rankdir BT -S `
    -o "tools/modelos_curso.png" curso
```


- graficar modelos de app inscripcion
```
python manage.py graph_models `
    --arrow-shape normal --hide-edge-labels --rankdir BT -S `
    -o "tools/modelos_inscripcion.png" inscripcion
```


- graficar modelos de app matrícula por partes
```
python manage.py graph_models `
    --arrow-shape normal --hide-edge-labels --rankdir BT -S --disable-abstract-fields `
    -o "tools/modelos_matricula_prep.png" matricula pagos `
    -I ProcesoMatricula,Valor*,Postulante*,ViaIngreso,*Productos,Periodo* `
    -x promedio_NEM,puntaje_NEM,puntaje_ranking,puntaje_matematica,puntaje_lenguaje,promedio_lenguaje_matematica,percentil_lenguaje_matematica,puntaje_historia,puntaje_ciencias,modulo_ciencias,puntaje_ponderado,marca,numero_serie,destacado,numero_vistas,estado,descripcion_larga,unidad_medida,stock

python manage.py graph_models `
    --arrow-shape normal --hide-edge-labels --rankdir BT -S --disable-abstract-fields `
    -o "tools/modelos_matricula_proceso.png" matricula pagos  `
    -I ProcesoMatricula,EtapaMatricula,MatriculaEstudiante,ArancelEstudiante,TNEEstudiante,GratuidadEstudiante,InhabilitantesMatricula,EtapaEstudiante,EstudianteRespondeEncuesta,OrdenCompra,FormaPago
```


- graficar modelos de app pagos
```
python manage.py graph_models `
    --arrow-shape normal --hide-edge-labels --rankdir BT -S --disable-abstract-fields `
    -o "tools/modelos_pagos.png" pagos `
    -I *Pago,OrdenCompra,*Productos,OrdenCompraDetalle,PagoWebPay
```

- graficar modelos de app pagaré
```
python manage.py graph_models `
    --arrow-shape normal --hide-edge-labels --rankdir BT -S --disable-abstract-fields `
    -o "tools/modelos_pagare.png" pagare `
    -X ModeloRegistraFechas,ProcesoMatricula,Plan,Persona,Comuna `
    -I ModalidadCuotaPagare,Pagare,ArancelEstudiante `
    -x interes_mensual_mora,decreto,decreto_ano,numero_cuotas,monto_total_extras
```
