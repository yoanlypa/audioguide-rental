#!/usr/bin/env bash
python manage.py migrate --noinput
python manage.py createsuperuser --noinput || true
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
