# Uaysen Online - Backend

Este proyecto consiste en el backend de la plataforma uaysen online. Corre sobre Python con Django y expone una API REST utilizando django-rest-framework.



## Cómo ejecutar el servidor de Desarrollo

Este servidor cuenta con hot reload y además se encarga de servir archivos estáticos y de media. Se recomienda utilizarlo para el desarrollo ya que todos los cambios se ven reflejados inmediatamente.


### Requisitos

- python 3.8


### Preparación

- Crear ambiente virtual

```
python -m venv .env

.env\Scripts\activate (en windows)
source .env/bin/activate (en linux)
```

- Instalar dependencias

```
(.env) pip install -r requirements.txt
```

- Ejecutar las migraciones de la base de datos

```
(.env) python manage.py migrate
```

- Agregar archivo de secretos de google auth

ir a la [consola de desarrolladores de google](https://console.developers.google.com/apis/credentials)
en la sección de credenciales, descargar el archivo secreto de *IDs de cliente de OAuth 2.0*
(client_secret_NNN.json) y colocarlo en la carpeta `config/`


### Correr el servidor de desarrollo

```
(.env) python manage.py runserver
```


### Administración

- crear un superusuario

```
python manage.py createsuperuser
```

- realizar un respaldo de la base de datos (excluyendo modelos no esenciales)

```
tools/respaldar_datos.sh
```

En este archivo se puede modificar el comando para exlcuir modelos, modificar el formato, entre otros.

- cargar un respaldo de la base de datos

```
python manage.py loaddata <archivo_respaldo>.json
```



## Cómo ejecutar utilizando Docker

Para ejecutar el proyecto en Docker se utilizan 3 contenedores descritos a continuación:

- postgresdb: ejecuta la base de datos del sistema.
- django: se encarga de correr el framework web Django.
- nginx: se encarga de enviar los requests al contenedor de django y servir los archvos de media y estáticos.

Este servidor no cuenta con hot reload por lo que cada vez que se haga un cambio se deberá compilar nuevamente el proyecto para que estos se vean reflejados.


### Requisitos

- Docker


### Preparación

- preparar el archivo con las variables de ambiente

para ello se puede crear una copia del archivo template.env a .env y luego editar las variables en la copia creada.

```
cp config/template.env config/.env
```

Las variables necesarias son:

```
# ubicacion de la base de datos (nombre del contenedor de docker)
DATABASE_HOST - la ubicación de la base de datos (nombre del contenedor de django).

# configuracion de la base de datos
DATABASE_PORT - el puerto para conectarse a la base de datos.
POSTGRES_USER - el usuario para la base de datos.
POSTGRES_PASSWORD - la contraseña para acceder a la base de datos.
POSTGRES_DB - el nombre de la base de datos.

# configuracion de django
DJANGO_DEBUG - flag que define si correr django en modo debug o no.
DJANGO_SECRET_KEY - la llave secreta de django.
DJANGO_DB_ENGINE - el motor de base de datos que usará django.
DJANGO_ALLOWED_HOSTS - los dominios donde esta app puede correr (e.g. www.uaysen.cl)

DJANGO_URL_MATRICULA - url del frontend de matrícula
DJANGO_URL_SGA - url del frontend del SGA
DJANGO_URL_BACKEND - url donde está corriendo la app

# configuracion para webpay
DJANGO_WEBPAY_CODIGO_COMERCIO
DJANGO_WEBPAY_API_KEY
DJANGO_WEBPAY_TIPO_INTEGRACION

# configuración de mail
DJANGO_MAIL_USER
DJANGO_MAIL_PASSWORD

# configuración de google cloud platform
DJANGO_GOOGLE_ADMIN_ACCOUNT - la cuenta de un usuario con permisos para crear y editar usuarios y unidades organizativas
DJANGO_SPREADSHEET_ENCUESTA_ID - el id del spreadsheet para la encuesta de caracterización

# integración con API ucampus
DJANGO_UCAMPUS_API
DJANGO_UCAMPUS_USER
DJANGO_UCAMPUS_PASS
```

- Agregar archivo de secretos de google auth

ir a la [consola de desarrolladores de google](https://console.developers.google.com/apis/credentials)
en la sección de credenciales, descargar el archivo secreto de *IDs de cliente de OAuth 2.0*
(client_secret_NNN.json) y colocarlo en la carpeta `config/`


### Correr docker compose

Docker comnpose se encarga de levantar y conectar todos los contenedores necesarios para el proyecto.

```
docker-compose up -d --build
```

El flag `-d` indica que se debería desvincular el output de los procesos de la terminal actual y el
flag `--build` que se debería volver a compilar la imagen del proyecto.

Este comando levanta 3 contenedores:

- **postgresdb** que contiene la base de datos y expone el puerto 5432 para conectarse a ella desde la máquina.
- **django** que contiene el proceso de django (detrás de gunicorn).
- **nginx** que contiene el servidor de nginx y expone en el puerto 8000 a aplicación.


### Administración

- crear un superusuario

```
docker-compose run django python manage.py createsuperuser
```

- realizar un respaldo de la base de datos (excluyendo modelos no esenciales)

```
tools/respaldar_datos_docker.sh
```

En este archivo se puede modificar el comando para exlcuir modelos, modificar el formato, entre otros.

- cargar un respaldo de la base de datos

```
tools/cargar_datos_docker.sh <archivo_respaldo>.json
```

- Conexión a la base de datos

```
psql -h <HOST> -p 5432 -d <POSTGRES_DB> -U <POSTGRES_USER>
```

y luego ingresar la contraseña en `<POSTGRES_PASSWORD>`
