import tempfile
from pathlib import Path
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.db import DatabaseError
from django.test import TestCase, SimpleTestCase, override_settings
from config.render_preflight import verify_render_runtime


@override_settings(ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=True,
                   NETLIFY_PROXY_SECRET='test-only-proxy-signing-key-long-enough-123')
class RenderReadinessTests(TestCase):
    def test_health_works_without_proxy_signature_and_checks_database(self):
        response = self.client.get('/_health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status':'ok'})
        self.assertIn('no-store', response['Cache-Control'])
        # Other insecure requests still redirect; HTTPS API access needs a signature.
        self.assertEqual(self.client.get('/api/public/').status_code, 301)
        self.assertEqual(self.client.get('/api/public/', secure=True).status_code, 403)
        self.assertEqual(self.client.post('/_health/').status_code, 405)

    def test_database_failure_is_unhealthy_without_disclosing_exception(self):
        with patch('core.views.Company.objects.filter', side_effect=DatabaseError('private database details')):
            response = self.client.get('/_health/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status':'unavailable'})
        self.assertNotIn('private database', response.content.decode())


class RenderDatabaseTests(SimpleTestCase):
    def setUp(self):
        self.env = {
            'RENDER':'true', 'DEBUG':'false',
            'SECRET_KEY':'testing-only-signing-key-long-enough-123',
            'NETLIFY_PROXY_SECRET':'testing-only-proxy-key-long-enough-123',
            'RENDER_EXTERNAL_HOSTNAME':'test.onrender.com',
            'CSRF_TRUSTED_ORIGINS':'https://estmajo-engineering-solutions.netlify.app',
            'DATABASE_URL':'postgresql://test:local-test-password@ep-test-pooler.eu-central-1.aws.neon.tech/company?sslmode=require',
        }

    def test_external_postgresql_tls_and_pooler_configuration(self):
        config = verify_render_runtime(self.env)
        self.assertEqual(config['ENGINE'], 'django.db.backends.postgresql')
        self.assertEqual(config['OPTIONS']['sslmode'], 'verify-full')
        self.assertTrue(config['DISABLE_SERVER_SIDE_CURSORS'])
        self.assertEqual(config['CONN_MAX_AGE'], 0)

    def test_no_ephemeral_sqlite_or_insecure_production_config(self):
        for changes in ({'DATABASE_URL':''}, {'DATABASE_URL':'sqlite:///tmp/company.db'},
                        {'DATABASE_URL':self.env['DATABASE_URL'].replace('require','disable')},
                        {'DEBUG':'true'}, {'NETLIFY_PROXY_SECRET':''}, {'SECRET_KEY':''},
                        {'RENDER_EXTERNAL_HOSTNAME':''}, {'CSRF_TRUSTED_ORIGINS':''}):
            with self.assertRaises(ImproperlyConfigured):
                verify_render_runtime({**self.env, **changes})

    def test_direct_endpoint_must_match_database_and_role(self):
        direct = self.env['DATABASE_URL'].replace('-pooler.', '.')
        verify_render_runtime({**self.env, 'DATABASE_URL_DIRECT':direct})
        with self.assertRaises(ImproperlyConfigured):
            verify_render_runtime({**self.env, 'DATABASE_URL_DIRECT':direct.replace('/company','/other')})

    def test_credentials_are_decoded_but_never_in_errors(self):
        from config.database import postgres_database
        config=postgres_database('postgresql://admin:p%40ss%3Aword@localhost/company?sslmode=disable', debug=True)
        self.assertEqual(config['PASSWORD'], 'p@ss:word')
        with self.assertRaises(ImproperlyConfigured) as error:
            postgres_database('postgresql://admin:never-expose-this@host/company?sslmode=disable')
        self.assertNotIn('never-expose-this', str(error.exception))
