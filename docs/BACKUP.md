# PostgreSQL backup, restoration and data transfer

The approved hosted database is now Neon PostgreSQL. It stores company settings, services/projects, users, password hashes, sessions, enquiries and media references. ImageKit stores the actual image/video/PDF files. Back up both separately. The older SQLite instructions below apply only to local development or an existing self-hosted disk installation.

## PostgreSQL exports

Use a trusted private computer with Python dependencies and PostgreSQL client tools installed. Use a pg_dump client at least as new as the hosted PostgreSQL major version. Configure DATABASE_URL and DATABASE_URL_DIRECT privately, never through chat, source control or command-line connection strings. Use the Neon direct endpoint for backups. From backend:

```bash
python manage.py backup_postgres /absolute/private/company-YYYYMMDD-HHMMSS.dump
```

Replace the timestamp before running. The command refuses to overwrite a file, writes owner-only permissions, invokes pg_dump without credentials in command arguments, and removes failed partial output. It reports a failed export without echoing provider errors or credentials. Backups are created on the computer running the command, not on ephemeral Render storage. Inspect the archive with `pg_restore --list`, then encrypt it and store it independently of Neon. Keep daily backups and a backup before each code/database update; agree a retention policy and test it. This command requires actual PostgreSQL client tools and live connection verification.

## Restore safely

Restore first into a separate empty test PostgreSQL database or Neon branch, never over the only production database. Configure the PostgreSQL client securely through private PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD, PGSSLMODE and PGSSLROOTCERT settings (or a restricted pgpass/service configuration). Do not put the password/connection string in pg_restore arguments. With those variables pointing to the test database:

```bash
pg_restore --no-owner --no-acl --dbname=TARGET_DATABASE_NAME /absolute/private/company-selected.dump
```

TARGET_DATABASE_NAME is the non-secret database name, not a URL. Verify the restore, migrations, company details, accounts, content, enquiries and asset references. For a production recovery, coordinate a maintenance window, block writes, preserve the current state, restore to the intended recovery database, then securely update the Render database URLs and restart. Validate owner access and public settings before reopening writes. Review restored sessions after a security incident. No hosted restore drill has yet been performed.

## Transfer an existing SQLite installation

If an earlier real installation has data, stop writes and make a consistent SQLite backup before exporting it. On a trusted private machine using the earlier database configuration:

```bash
python manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --exclude sessions --exclude core.ratebucket --output /absolute/private/company-transfer.json
```

The JSON includes private enquiries and password hashes: restrict permissions to the owner, encrypt it and never commit or publish it. Point the same source version privately at the new empty PostgreSQL database, run migrations, then `python manage.py loaddata /absolute/private/company-transfer.json`. Migrations provide permission/content-type records; fixture import updates seeded company rows and resets model sequences. Check object counts and real records before changing the public backend origin. Existing sessions and rate windows are deliberately excluded. Do not assume a transfer has occurred merely because the code supports PostgreSQL.

## Media originals

Export ImageKit originals independently and retain their matching database backup. Restoring PostgreSQL cannot recover permanently deleted remote files. Free provider plans and branch/history features are subject to account limits and do not replace offsite backups.

## Legacy SQLite workflow

### SQLite backup and restoration

The SQLite database contains company settings, content, document/media references, enquiries, user password hashes and sessions. Image/video/PDF file bytes live in ImageKit. Back up both the database and the media originals/provider account separately.

## Create a consistent snapshot

Use the provided SQLite online-backup command, which works with an active application and checks the resulting database. Do not copy a database file while writes are in progress.

```bash
docker compose exec app python manage.py backup_database /data/backups/company-2026-10-21.sqlite3
docker compose cp app:/data/backups/company-2026-10-21.sqlite3 ./company-2026-10-21.sqlite3
```

Use a unique filename for every backup. The command refuses to overwrite an existing file. Keep at least daily backups and a backup before every source update. Copy snapshots off the server to a restricted encrypted location; snapshots inside the same volume do not protect against disk loss. Establish a retention policy for enquiry data and remove old backups according to that policy. Secure environment files separately; never store them in the public website or repository.

For local development:

```bash
DEBUG=true SECRET_KEY=local-backup-command-only-key-at-least-32-characters .venv/bin/python backend/manage.py backup_database /absolute/private/backup.sqlite3
```

## Restore

Use a maintenance window. Check that the backup matches the intended installation before restoring. Retain a copy of the current database first.

```bash
# Stop writes and keep the server stopped during the copy.
docker compose stop app
# Copy the selected verified snapshot into the persistent volume via a one-off container.
docker compose run --rm --no-deps --user root -v /absolute/private/backup.sqlite3:/restore.sqlite3:ro app sh -c 'cp /restore.sqlite3 /data/db.sqlite3 && chown 10001:10001 /data/db.sqlite3 && chmod 600 /data/db.sqlite3 && rm -f /data/db.sqlite3-wal /data/db.sqlite3-shm'
# Check integrity before starting the public application.
docker compose run --rm --no-deps app python -c 'import sqlite3; c=sqlite3.connect("/data/db.sqlite3"); result=c.execute("PRAGMA integrity_check").fetchone()[0]; print(result); assert result == "ok"'
docker compose up -d app
```

Use the source version compatible with the restored schema; the application start runs forward migrations. Do not attempt an unplanned schema downgrade. Verify owner login, settings, services, project references, enquiries and media downloads after restoration. For a security incident, invalidate restored sessions and rotate credentials as appropriate.

## Media backup and orphan handling

ImageKit is the durable object store for all uploaded photographs, videos and PDF documents. Maintain provider account ownership and billing, export originals on a regular schedule, and retain the corresponding database snapshot. Deleting a remote asset cannot be repaired by restoring SQLite alone.

Use `docker compose exec app python manage.py media_audit` to produce a read-only list of remote `/esmajo` files absent from SQLite and local media without references. Review file IDs and provider logs before manually cleaning remote orphans; files may be shared outside this application. The normal dashboard deletion checks all application references and blocks shared-file deletion.

A real server restore drill and provider-original export were not performed in this session. Perform them before relying on the backup plan for production recovery.
