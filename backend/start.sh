#!/usr/bin/env bash
set -e

python manage.py migrate --noinput

# Crea el admin solo si NO existe (exit-code 1 se ignora)
python manage.py createsuperuser --noinput \
  --username "$DJANGO_SUPERUSER_USERNAME" \
  --email "$DJANGO_SUPERUSER_EMAIL" || true      # <- clave

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}
