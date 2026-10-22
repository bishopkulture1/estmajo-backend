#!/usr/bin/env bash
set -euo pipefail
umask 077
python -m config.render_preflight
# Use Neon's direct endpoint for schema/setup operations when supplied.
DATABASE_URL="${DATABASE_URL_DIRECT:-$DATABASE_URL}" python manage.py migrate --noinput
DATABASE_URL="${DATABASE_URL_DIRECT:-$DATABASE_URL}" python manage.py seed_services
DATABASE_URL="${DATABASE_URL_DIRECT:-$DATABASE_URL}" python manage.py bootstrap_owner
python manage.py check --deploy --fail-level ERROR
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-10000}" \
  --workers 1 --threads 4 --timeout 240 --graceful-timeout 240 \
  --access-logfile - --error-logfile - --capture-output
