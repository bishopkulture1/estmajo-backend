import io
import os
import uuid
from unittest.mock import patch, Mock
import requests
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from core.models import Company, Enquiry
from core.views import notify


class BootstrapOwnerTests(TestCase):
    def setUp(self):
        Company.current()
        self.env={'BOOTSTRAP_ADMIN_USERNAME':'company-owner','BOOTSTRAP_ADMIN_PASSWORD':'Owner-Initial-Secure-Password-842','BOOTSTRAP_ADMIN_EMAIL':'owner@example.com'}

    def run_bootstrap(self):
        output=io.StringIO()
        call_command('bootstrap_owner', stdout=output)
        return output.getvalue()

    def test_private_bootstrap_creates_hashed_owner_and_does_not_reset(self):
        with patch.dict(os.environ, self.env): output=self.run_bootstrap()
        owner=get_user_model().objects.get(username='company-owner')
        self.assertTrue(owner.is_staff and owner.is_superuser)
        self.assertTrue(owner.check_password(self.env['BOOTSTRAP_ADMIN_PASSWORD']))
        self.assertNotIn(self.env['BOOTSTRAP_ADMIN_PASSWORD'],output)
        with patch.dict(os.environ, {**self.env,'BOOTSTRAP_ADMIN_PASSWORD':'Different-Secret-Password-344'}): self.run_bootstrap()
        owner.refresh_from_db()
        self.assertTrue(owner.check_password(self.env['BOOTSTRAP_ADMIN_PASSWORD']))
        self.assertEqual(get_user_model().objects.count(),1)

    def test_no_default_account_and_invalid_credentials_fail_safely(self):
        with patch.dict(os.environ, {'BOOTSTRAP_ADMIN_USERNAME':'','BOOTSTRAP_ADMIN_PASSWORD':'','BOOTSTRAP_ADMIN_EMAIL':''}):
            self.run_bootstrap()
        self.assertFalse(get_user_model().objects.exists())
        for updates in ({'BOOTSTRAP_ADMIN_PASSWORD':'short'}, {'BOOTSTRAP_ADMIN_EMAIL':'bad-email'}, {'BOOTSTRAP_ADMIN_USERNAME':'invalid name!'}):
            with patch.dict(os.environ, {**self.env,**updates}):
                with self.assertRaises(CommandError): self.run_bootstrap()
        self.assertFalse(get_user_model().objects.exists())

    def test_existing_inactive_administrator_also_blocks_bootstrap(self):
        get_user_model().objects.create_user('existing', is_staff=True, is_active=False)
        with patch.dict(os.environ, self.env): self.run_bootstrap()
        self.assertFalse(get_user_model().objects.filter(username='company-owner').exists())


@override_settings(EMAIL_BACKEND='core.email_backend.ResendEmailBackend', RESEND_API_KEY='test-key-not-real', DEFAULT_FROM_EMAIL='website@example.com')
class HTTPSNotificationTests(TestCase):
    def setUp(self):
        company=Company.current();company.enquiry_recipient='company@example.com';company.save()
        self.enquiry=Enquiry.objects.create(token=uuid.uuid4(), name='Visitor', email='visitor@example.com', subject='Quote request', message='Please contact me about a project.')

    def status(self):
        self.enquiry.refresh_from_db()
        return self.enquiry.status

    @patch('core.email_backend.requests.post')
    def test_verified_sender_reply_to_and_stable_retry_key(self, post):
        post.return_value=Mock(status_code=200,json=Mock(return_value={'id':'provider-email-id'}))
        notify(self.enquiry.pk)
        self.assertEqual(self.status(),'accepted')
        first=post.call_args
        self.assertEqual(first.args[0],'https://api.resend.com/emails')
        self.assertEqual(first.kwargs['json']['from'],'website@example.com')
        self.assertEqual(first.kwargs['json']['reply_to'],['visitor@example.com'])
        self.assertEqual(first.kwargs['json']['to'],['company@example.com'])
        self.assertFalse(first.kwargs['allow_redirects'])
        Enquiry.objects.filter(pk=self.enquiry.pk).update(status='unknown')
        notify(self.enquiry.pk,force=True)
        self.assertEqual(first.kwargs['headers']['Idempotency-Key'],post.call_args.kwargs['headers']['Idempotency-Key'])
        self.assertEqual(Enquiry.objects.count(),1)

    @patch('core.email_backend.requests.post')
    def test_explicit_rejection_and_ambiguous_timeout_are_different(self, post):
        post.return_value=Mock(status_code=422)
        notify(self.enquiry.pk)
        self.assertEqual(self.status(),'failed')
        post.side_effect=requests.Timeout('private credential details must not reach a public response')
        notify(self.enquiry.pk)
        self.assertEqual(self.status(),'unknown')
        self.assertNotIn('private credential',self.enquiry.last_error)
        self.assertEqual(Enquiry.objects.count(),1)

    @patch('core.email_backend.requests.post')
    def test_no_provider_id_is_not_confirmed_acceptance(self, post):
        post.return_value=Mock(status_code=200,json=Mock(return_value={}))
        notify(self.enquiry.pk)
        self.assertEqual(self.status(),'unknown')

    @override_settings(RESEND_API_KEY='')
    @patch('core.email_backend.requests.post')
    def test_missing_configuration_keeps_saved_enquiry_without_http_call(self, post):
        notify(self.enquiry.pk)
        self.assertEqual(self.status(),'failed')
        post.assert_not_called()
        self.assertEqual(Enquiry.objects.count(),1)

    @override_settings(DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':'company'}})
    def test_sqlite_backup_command_rejects_postgresql(self):
        with self.assertRaisesMessage(CommandError,'PostgreSQL'):
            call_command('backup_database','/tmp/not-a-postgresql-backup.sqlite3')

class PostgresBackupTests(TestCase):
    def test_backup_keeps_credentials_out_of_arguments_and_refuses_overwrite(self):
        import tempfile
        from pathlib import Path
        from django.conf import settings
        config={'ENGINE':'django.db.backends.postgresql','HOST':'database.example.com','PORT':5432,'NAME':'company','USER':'owner','PASSWORD':'private-backup-password','OPTIONS':{'sslmode':'verify-full'}}
        def export(*args, **kwargs):
            self.assertNotIn('private-backup-password',repr(args))
            self.assertEqual(kwargs['env']['PGPASSWORD'],'private-backup-password')
            kwargs['stdout'].write(b'PGDMP test archive')
            return Mock(returncode=0)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'company.dump'
            with patch.dict(settings.DATABASES, {'default':config}), patch.dict(os.environ,{'DATABASE_URL_DIRECT':''}), patch('core.management.commands.backup_postgres.shutil.which',return_value='/usr/bin/pg_dump'), patch('core.management.commands.backup_postgres.subprocess.run',side_effect=export):
                call_command('backup_postgres',str(path),stdout=io.StringIO())
                self.assertEqual(path.stat().st_mode & 0o777,0o600)
                with self.assertRaisesMessage(CommandError,'exists'):
                    call_command('backup_postgres',str(path),stdout=io.StringIO())
            self.assertEqual(path.read_bytes(),b'PGDMP test archive')

    def test_failed_export_removes_partial_and_withholds_private_errors(self):
        import tempfile
        from pathlib import Path
        from django.conf import settings
        config={'ENGINE':'django.db.backends.postgresql','HOST':'database.example.com','NAME':'company','USER':'owner','PASSWORD':'secret','OPTIONS':{}}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'failed.dump'
            with patch.dict(settings.DATABASES, {'default':config}), patch.dict(os.environ,{'DATABASE_URL_DIRECT':''}), patch('core.management.commands.backup_postgres.shutil.which',return_value='/usr/bin/pg_dump'), patch('core.management.commands.backup_postgres.subprocess.run',return_value=Mock(returncode=1,stderr=b'private credentials')):
                with self.assertRaises(CommandError) as error:
                    call_command('backup_postgres',str(path))
                self.assertNotIn('private credentials',str(error.exception))
            self.assertFalse(path.exists())
