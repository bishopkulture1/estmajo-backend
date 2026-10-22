"""Parse PostgreSQL configuration without leaking credentials in errors."""
from urllib.parse import urlsplit, unquote, parse_qs
from django.core.exceptions import ImproperlyConfigured
import certifi


def postgres_database(url, debug=False):
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('postgres', 'postgresql') or not parsed.hostname or not parsed.username or not parsed.password or not parsed.path.strip('/'):
            raise ValueError
        port = parsed.port or 5432
        query = parse_qs(parsed.query)
        local = parsed.hostname in ('localhost', '127.0.0.1', '::1')
        sslmode = query.get('sslmode', ['verify-full'])[0]
        if debug and local and sslmode == 'disable':
            options = {'sslmode':'disable', 'connect_timeout':10}
        else:
            if sslmode not in ('require', 'verify-ca', 'verify-full'):
                raise ValueError
            # Strengthen Neon URLs using sslmode=require with CA/hostname verification.
            options = {'sslmode':'verify-full', 'sslrootcert':certifi.where(), 'connect_timeout':10}
        if 'channel_binding' in query:
            binding = query['channel_binding'][0]
            if binding not in ('prefer', 'require'):
                raise ValueError
            options['channel_binding'] = binding
        return {
            'ENGINE':'django.db.backends.postgresql',
            'NAME':unquote(parsed.path.lstrip('/')), 'USER':unquote(parsed.username),
            'PASSWORD':unquote(parsed.password), 'HOST':parsed.hostname, 'PORT':port,
            'CONN_MAX_AGE':0, 'CONN_HEALTH_CHECKS':True,
            'DISABLE_SERVER_SIDE_CURSORS':True, 'OPTIONS':options,
        }
    except (ValueError, TypeError):
        raise ImproperlyConfigured('DATABASE_URL must be a complete PostgreSQL connection URL with TLS. Its value is never displayed.') from None
