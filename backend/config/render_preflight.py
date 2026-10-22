"""Render Free uses an external PostgreSQL database; never ephemeral SQLite."""
import os
from django.core.exceptions import ImproperlyConfigured
from .database import postgres_database


def verify_render_runtime(environ=None):
    env = os.environ if environ is None else environ
    if env.get('RENDER') != 'true':
        raise ImproperlyConfigured('Use this startup script only in the Render runtime.')
    if env.get('DEBUG', 'false').lower() != 'false':
        raise ImproperlyConfigured('DEBUG must be false on Render.')
    if len(env.get('SECRET_KEY', '')) < 32 or len(env.get('NETLIFY_PROXY_SECRET', '')) < 32:
        raise ImproperlyConfigured('Configure permanent SECRET_KEY and NETLIFY_PROXY_SECRET values of at least 32 random characters.')
    if not env.get('RENDER_EXTERNAL_HOSTNAME'):
        raise ImproperlyConfigured('Render did not provide the service hostname.')
    if 'https://estmajo-engineering-solutions.netlify.app' not in [v.strip() for v in env.get('CSRF_TRUSTED_ORIGINS', '').split(',')]:
        raise ImproperlyConfigured('Trust the existing ESTMAJO Netlify HTTPS origin for CSRF.')
    if not env.get('DATABASE_URL'):
        raise ImproperlyConfigured('Configure external PostgreSQL DATABASE_URL. SQLite is not permitted on Render Free.')
    database = postgres_database(env['DATABASE_URL'])
    if env.get('DATABASE_URL_DIRECT'):
        direct = postgres_database(env['DATABASE_URL_DIRECT'])
        if (direct['NAME'], direct['USER'], direct['HOST'].replace('-pooler.', '.')) != (database['NAME'], database['USER'], database['HOST'].replace('-pooler.', '.')):
            raise ImproperlyConfigured('DATABASE_URL_DIRECT must point to the same Neon database and role as DATABASE_URL.')
    return database


if __name__ == '__main__':
    verify_render_runtime()
    print('Render security and external PostgreSQL configuration checks passed.')
