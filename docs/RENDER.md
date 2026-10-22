# Free Render backend + Neon PostgreSQL + ImageKit

The owner approved switching the hosted database from SQLite to PostgreSQL to avoid paid Render disks. This is now the default Render deployment in `render.yaml`. SQLite remains an option for local development and the older self-hosted Docker deployment.

## Current status

The free-tier configuration and source changes are prepared. The Neon Free project `estmajo-engineering` has been created in Frankfurt with a `production` branch and `company` PostgreSQL database. A read-only Neon query confirms PostgreSQL 17.11 and the expected database/role. Django tables are not yet created: this execution workspace cannot resolve the Neon PostgreSQL hostname for a direct connection. No Render web service has been created, and no live backend URL is claimed. The published Netlify site remains the labelled public preview until the full-source deployment is connected.

Required activation inputs are the confirmed Render workspace, a Git repository containing this source with appropriate write/deploy access, the connected Neon database configuration and private integration configuration. No paid resources or upgrades are authorised. Free plans have usage limits and can suspend; no promise of unlimited or permanently free capacity is made.

## Components

| Component | Purpose |
| --- | --- |
| Existing Netlify site | Public React website and React owner dashboard |
| Render Free web service | Django/DRF API, one worker and four threads |
| Neon Free PostgreSQL | Persistent company content, accounts, sessions, media references and enquiries |
| ImageKit account | Uploaded image, video and PDF file bytes |
| Resend HTTPS API | Optional configured enquiry email notifications; standard SMTP is blocked on Render Free |

There is no Render disk and no expiring Render Free Postgres database in this Blueprint. Neon is a separate external PostgreSQL service. Confirm its account remains on the Free plan and monitor its quotas before and after provisioning.

Render Free sleeps after 15 idle minutes; the next wake-up can take around a minute. It also lacks interactive shell access and blocks SMTP ports 25/465/587. The app retries only safe public/session GET requests during startup, never content writes or enquiry submissions. The Netlify production build allows time for the sleeping backend to wake up and still refuses publication if signed API verification fails. Cold starts, provider quotas and large upload limits must be checked on the real services; this is not an always-on availability guarantee.

## Source repository and Render creation

Extract the source ZIP. Put the **contents of its `esmajo` folder** at the Git repository root, with `render.yaml`, `netlify.toml`, `backend` and `frontend` at the top level. Use real source files rather than PDFs or the ZIP archive. Do not commit private `.env` files, database exports, backups or passwords. The `.gitignore` excludes these.

Use the intended private GitHub/GitLab/Bitbucket repository with Render access. If using the existing `estmajo-frontend` repository, upload this full project structure; its name alone does not make it backend-ready. The current connected GitHub permission was read-only when preparation ran, so this update was not pushed there.

In the confirmed Render workspace, create a Blueprint from that repository using root `render.yaml`. Review that the plan is **Free** and that there is **no disk or Render database**. Proposed region is Frankfurt. Automatic code deploys are off for controlled updates. No resource should be created until its source, workspace and Free plan have been verified.

The Blueprint uses Python 3.12.15 and the exact dependency lockfile. Build installs requirements and collects static assets using a disposable local SQLite path without touching the real database. Startup requires external PostgreSQL, runs migrations and initial setup, then starts Gunicorn on Render's assigned `PORT`. Missing or insecure database settings stop startup rather than silently creating ephemeral SQLite.

## Neon database configuration

Create a PostgreSQL project under the intended Neon account's Free plan, preferably in a region near the Render service. Store its connection strings directly in Render's private Environment settings:

```dotenv
DATABASE_URL=
DATABASE_URL_DIRECT=
```

Use Neon's pooled URL for `DATABASE_URL` and its unpooled/direct URL for `DATABASE_URL_DIRECT`. Both must identify the same database and database role. Do not paste the strings into chat, public company settings or `VITE_` variables.

The backend enforces TLS certificate/hostname verification using the bundled CA set, uses short-lived connections, and disables server-side cursors for transaction-pool compatibility. URL-escaped credentials are decoded safely. Migrations and one-time setup use the direct URL when supplied. A bad URL does not appear in validation errors. The real Neon TLS connection and database permissions must be tested during activation.

Django migrations create the same persistent models, including session/auth tables. No production data has been migrated by this source change. If an earlier real SQLite database contains owner edits or enquiries, follow BACKUP.md to export and transfer it before switching the production origin.

## Security and Netlify connection

Render generates a permanent `SECRET_KEY`; keep it stable across restarts. Set a random `NETLIFY_PROXY_SECRET` of at least 32 characters in Render and the exact same value in Netlify's private build/runtime environment. Keep `DEBUG=false` and the existing Netlify origin in `CSRF_TRUSTED_ORIGINS`. The exact Render service hostname is automatically added to `ALLOWED_HOSTS`; custom backend hostnames must be added explicitly.

Link the complete source to the **existing** Netlify project, preserving its hostname. Set `DJANGO_API_ORIGIN` to the exact Render HTTPS origin after deployment; never invent the assigned service URL. Use the root `netlify.toml` and a supported Node version such as Node 24. Production build explicitly disables `VITE_PUBLIC_PREVIEW` and deploys the signed API Edge Function. A static Drop upload cannot activate that function or the backend.

Cookies stay scoped to the Netlify website and remain HTTP-only, Secure and SameSite=Lax. CSRF validation still applies. Unsigned direct `/api/` calls return 403. `/_health/` checks database readability without disclosing company details, credentials or exceptions.

## Initial owner account without Render Shell

Render Free does not provide an interactive shell. Configure these privately in Render before the first successful startup:

```dotenv
BOOTSTRAP_ADMIN_USERNAME=
BOOTSTRAP_ADMIN_EMAIL=
BOOTSTRAP_ADMIN_PASSWORD=
```

Choose a unique valid username and a strong password of at least 12 characters. Email is optional. No credentials are shipped or assumed. The startup command `bootstrap_owner` creates the first active staff/superuser only when no staff or superuser account already exists. It hashes the password and does not log it. An existing administrator, including an inactive one, prevents this bootstrap from resetting or replacing accounts.

After a successful private owner login at Netlify `/owner`, remove `BOOTSTRAP_ADMIN_PASSWORD` from Render and redeploy. The account persists in Neon. Later password changes use the dashboard and require the current password.

For recovery, the authorised administrator verifies the owner's identity, obtains the Neon direct connection through a secure channel on a trusted local machine, installs backend dependencies, sets private `DATABASE_URL` and `SECRET_KEY` environment values, and runs `python manage.py changepassword OWNER_USERNAME` from `backend`. The password is entered interactively. The local machine must use the same production database. This process does not require a paid Render shell. There is no public password-reset endpoint or backdoor; bootstrap never resets an existing account.

## ImageKit and email

Set these privately in Render:

```dotenv
IMAGEKIT_PRIVATE_KEY=
IMAGEKIT_URL_ENDPOINT=
EMAIL_BACKEND=core.email_backend.ResendEmailBackend
RESEND_API_KEY=
DEFAULT_FROM_EMAIL=
```

Use a sender verified/approved by the email provider. The public `estmajo@hotmail.com` remains a company contact and private enquiry recipient; it is not automatically a verified API sender. Configure provider verification before expecting automatic notifications. If no sender is ready, enquiries are still saved and mailto links remain available, but automatic notification delivery is not claimed.

The HTTPS backend sends the visitor's validated email as Reply-To, uses the authenticated sender, checks for the provider's accepted email ID and distinguishes explicit rejection from an uncertain timeout. Stable payload-based idempotency keys reduce duplicate notifications inside Resend's 24-hour deduplication window. A later retry can still duplicate a notification, so the dashboard's uncertainty confirmation remains in place. Accepted means provider acceptance, not inbox delivery. No real email has been sent in preparation tests.

Missing ImageKit credentials prevent uploads with an error rather than using local disk. Private uploads, signed transformations, metadata checks, shared-reference protection and video/PDF handling remain in place. Real account limits, uploads, playback and PDF downloads require live checks.

## Backup and verification

See BACKUP.md for private PostgreSQL exports, restoration and transfer from a previous SQLite database. Run backups from a trusted external machine with direct Neon access because Render Free has no durable backup filesystem, shell or cron access to a disk. Export ImageKit originals separately. Free-tier retention is not a substitute for independent backups.

Before announcing launch, verify: Render health; signed API access; initial owner login/logout/password change; company edits reflected publicly; data and sessions surviving Render restart; unpublished project privacy; real enquiry storage and notification acceptance/inbox receipt; actual ImageKit upload/playback/download; and backup restoration into a separate test database.

Prepared checks are listed in VERIFICATION.md. Real provisioning and end-to-end hosted verification remain pending.
