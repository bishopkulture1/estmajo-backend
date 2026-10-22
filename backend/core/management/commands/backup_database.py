import sqlite3, os
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
class Command(BaseCommand):
    help='Create a consistent SQLite snapshot using the online backup API (does not copy a live database file).'
    def add_arguments(self,parser):
        parser.add_argument('destination')
    def handle(self,*args,**options):
        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
            raise CommandError('This command is for local SQLite only. Back up PostgreSQL with pg_dump and a direct TLS database connection; see docs/BACKUP.md.')
        destination=Path(options['destination']).resolve()
        if destination.exists(): raise CommandError('Destination already exists; choose a new backup filename.')
        if str(destination)==str(Path(settings.DATABASES['default']['NAME']).resolve()): raise CommandError('Backup destination must be different from the live database.')
        destination.parent.mkdir(parents=True,exist_ok=True)
        descriptor=os.open(destination,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(descriptor)
        source=sqlite3.connect(settings.DATABASES['default']['NAME'])
        backup=sqlite3.connect(destination)
        try:
            source.backup(backup)
            check=backup.execute('PRAGMA integrity_check').fetchone()[0]
            if check!='ok': raise CommandError('Backup integrity check failed: '+check)
        finally: source.close();backup.close()
        self.stdout.write('Consistent backup saved: '+str(destination))
