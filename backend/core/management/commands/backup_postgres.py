"""Export PostgreSQL with pg_dump without putting credentials in command arguments."""
import os
import shutil
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from config.database import postgres_database


class Command(BaseCommand):
    help = 'Create a private PostgreSQL custom-format backup on this machine. Requires pg_dump.'

    def add_arguments(self, parser):
        parser.add_argument('destination')

    def handle(self, *args, **options):
        config = settings.DATABASES['default']
        if os.getenv('DATABASE_URL_DIRECT'):
            config = postgres_database(os.environ['DATABASE_URL_DIRECT'], settings.DEBUG)
        if config['ENGINE'] != 'django.db.backends.postgresql':
            raise CommandError('Configure PostgreSQL before using this backup command.')
        binary = shutil.which('pg_dump')
        if not binary:
            raise CommandError('Install PostgreSQL client tools on your private backup machine first.')
        destination = Path(options['destination']).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, 'PGHOST':str(config['HOST']), 'PGPORT':str(config.get('PORT',5432)),
               'PGDATABASE':config['NAME'], 'PGUSER':config['USER'], 'PGPASSWORD':config['PASSWORD'],
               'PGSSLMODE':config.get('OPTIONS',{}).get('sslmode','verify-full'),
               'PGSSLROOTCERT':config.get('OPTIONS',{}).get('sslrootcert',''), 'PGCONNECT_TIMEOUT':'15'}
        if config.get('OPTIONS',{}).get('channel_binding'):
            env['PGCHANNELBINDING'] = config['OPTIONS']['channel_binding']
        try:
            descriptor = os.open(destination, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
        except FileExistsError:
            raise CommandError('Backup destination exists; choose a unique filename.') from None
        try:
            with os.fdopen(descriptor, 'wb') as output:
                result = subprocess.run([binary, '--format=custom', '--no-owner', '--no-acl'], env=env,
                                        stdout=output, stderr=subprocess.PIPE, check=False)
                output.flush(); os.fsync(output.fileno())
            if result.returncode or destination.stat().st_size == 0:
                raise CommandError('PostgreSQL backup failed. Check client version, direct connection and database access privately.')
        except Exception:
            destination.unlink(missing_ok=True)  # Delete only the failed output created by this invocation.
            raise CommandError('PostgreSQL backup failed. No successful backup was created; credentials and provider output are withheld.') from None
        self.stdout.write('PostgreSQL backup created. Verify it with pg_restore --list and export it to restricted encrypted storage.')
