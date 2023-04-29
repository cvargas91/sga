#!/bin/sh

echo "Waiting for postgres..."
while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Migrating the database."
python manage.py migrate --noinput

echo "Collecting static assets."
python manage.py collectstatic --noinput

exec "$@"
