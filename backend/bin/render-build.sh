#!/usr/bin/env bash
set -euo pipefail
python -m pip install --disable-pip-version-check -r requirements.lock.txt
# Collect static assets without connecting to the production database or requiring secrets.
RENDER=false DATABASE_URL= DEBUG=true SECRET_KEY=build-only-placeholder-key-never-used-for-live-sessions \
  SQLITE_PATH=/tmp/estmajo-build-placeholder.sqlite3 python manage.py collectstatic --noinput
