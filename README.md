# ESTMAJO backend deployment

This repository contains the original Django backend from `ESTMAJO-Backend.zip`, with the original deployment reference documents and Render blueprint recovered from the supplied full source archive. Backend source files are preserved unchanged.

## Repository layout

- `backend/`: Django configuration, API, four migrations, tests, locked dependencies, administrator and backup commands.
- `backend/bin/render-build.sh`: dependency installation and static collection.
- `backend/bin/render-start.sh`: production checks, migrations, service seeding, first-owner bootstrap and Gunicorn.
- `render.yaml`: original Render Free blueprint; its root directory is `backend`.
- `docs/`: original project guides. These describe the former combined frontend/backend project and contain historical status reports, not newly verified deployment results. Use this README for this separate backend repository.

## Local verification

From the repository root, with Python 3.12:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock.txt
export DEBUG=true
export SECRET_KEY=local-testing-only-key-at-least-32-characters
.venv/bin/python backend/manage.py test core
.venv/bin/python backend/manage.py makemigrations --check --dry-run
```

Local tests use SQLite and mocked external integrations. They do not prove live PostgreSQL connectivity, mail delivery or ImageKit uploads.

## Render setup

Use `bishopkulture1/estmajo-backend`, branch `main`, in Isaiah's workspace. For the supplied blueprint use root `render.yaml`. For manual web-service setup use:

| Setting | Value |
| --- | --- |
| Runtime | Python |
| Root directory | `backend` |
| Build command | `bash bin/render-build.sh` |
| Start command | `bash bin/render-start.sh` |
| Health check | `/_health/` |
| Intended plan | Free, no disk |
| Intended region | Frankfurt |

The blueprint preserves the original runtime and platform settings. Review platform validation before applying it. Do not substitute SQLite for the external production database. No live deployment is implied by uploading this repository.

Configure actual secrets privately in Render, never in this repository:

- `DEBUG=false`.
- Permanent random `SECRET_KEY` and `NETLIFY_PROXY_SECRET`, each at least 32 characters. The blueprint can generate `SECRET_KEY`.
- `DATABASE_URL`: Neon PostgreSQL connection URL with TLS. Optional `DATABASE_URL_DIRECT` must use the same database and role for schema operations.
- `CSRF_TRUSTED_ORIGINS=https://estmajo-engineering-solutions.netlify.app`. The current startup check requires this exact origin. A new frontend domain needs a reviewed configuration/code update.
- `EMAIL_BACKEND=core.email_backend.ResendEmailBackend`, `RESEND_API_KEY` and a provider-approved `DEFAULT_FROM_EMAIL` for notifications.
- `IMAGEKIT_PRIVATE_KEY` and `IMAGEKIT_URL_ENDPOINT` for uploads.
- `BOOTSTRAP_ADMIN_USERNAME`, optional `BOOTSTRAP_ADMIN_EMAIL`, and a strong `BOOTSTRAP_ADMIN_PASSWORD` of at least 12 characters for initial owner creation.

Render supplies `RENDER`, `RENDER_EXTERNAL_HOSTNAME` and `PORT`. The settings add that exact hostname to allowed hosts. Add custom hosts explicitly through `ALLOWED_HOSTS` if needed.

Startup applies migrations, seeds services and creates the first owner only if no staff/superuser exists. It never resets an existing account. After verifying owner login through the frontend `/owner` page, remove `BOOTSTRAP_ADMIN_PASSWORD` from Render and redeploy.

## Frontend connection

The frontend requires the original Netlify Edge Function and build configuration from the separate full/frontend source. This backend repository alone does not deploy the frontend. Follow `docs/NETLIFY.md` for the proxy settings. Set its backend URL to the actual successful Render deployment URL, and configure the same private proxy secret on both platforms. Never expose that secret or database credentials in a `VITE_` variable. Unsigned direct API calls are intentionally rejected.

## Backup and restore

On a trusted external machine with PostgreSQL client tools and private production environment settings:

```bash
.venv/bin/python backend/manage.py backup_postgres /secure-backups/estmajo-unique.dump
pg_restore --list /secure-backups/estmajo-unique.dump
```

Use a compatible `pg_dump` version and a unique destination. Store exports in restricted encrypted storage outside this repository. Verify restoration into a separate test database before relying on a backup. `backup_database` is for the legacy SQLite setup; see `docs/BACKUP.md` for restore details and separate ImageKit asset backups. Do not keep backups on the ephemeral Render filesystem.

## Launch verification checklist

- [ ] Render build succeeds and startup migrations complete against Neon.
- [ ] `/_health/` returns healthy with the real database.
- [ ] Netlify signed proxy and CSRF/session flow work.
- [ ] Owner login, logout and password change work.
- [ ] Content changes persist after a Render restart.
- [ ] Enquiries persist; notification delivery is tested separately.
- [ ] ImageKit upload, playback and document download work.
- [ ] A backup restores successfully to a separate test database.

Repository upload verification and local test results must be reported separately from these live checks. Original guides: [Render](docs/RENDER.md), [administrator setup](docs/ADMIN_SETUP.md), [backup](docs/BACKUP.md), [architecture](docs/ARCHITECTURE.md).
