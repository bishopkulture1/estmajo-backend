# Backend and administrator activation

The complete Django/DRF backend and React owner workspace are included. The owner sign-in route is `/owner`. No administrator account or password is bundled in the download.

## Run and sign in locally

Follow README.md to install Python and Node dependencies and run `npm run dev`. That launcher applies migrations to SQLite and starts the API and React site together. From a second terminal, in the source root:

```bash
cd backend
DEBUG=true SECRET_KEY=local-development-setup-only-key-at-least-32-characters ../.venv/bin/python manage.py createsuperuser
```

Choose a unique username and strong password interactively. Open `http://localhost:4173/owner` and enter those credentials. This is the real Django authentication flow. Local development sessions are stored in SQLite; Render sessions are stored in PostgreSQL; passwords are hashed by Django. Do not use the documented development signing key for production.

## Deploy the backend on Render

Use RENDER.md and root `render.yaml` for Render Free with external Neon PostgreSQL. No paid disk is configured. Confirm the workspace and source repository, connect Neon and configure the private one-time BOOTSTRAP_ADMIN_* values. Render Free has no interactive shell.

## Connect the existing Netlify website

The published Netlify page contains the branded login design, with credential entry disabled while it is the public-only preview. It cannot authenticate without a running Django server.

1. Deploy the free Render service and Neon database following RENDER.md. Startup migrates PostgreSQL and creates the first owner only from private initial setup values.
2. Configure HTTPS, `DEBUG=false`, a permanent random `SECRET_KEY`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` including `https://estmajo-engineering-solutions.netlify.app`.
3. Configure matching `NETLIFY_PROXY_SECRET` values on Django and Netlify and set the real `DJANGO_API_ORIGIN` in Netlify. Follow NETLIFY.md for the signed same-origin API proxy. Keep these values in secure server/hosting settings, never public company fields or chat messages.
4. Deploy the full source using its root `netlify.toml`, rather than the static preview ZIP. The production build checks connectivity to Django first. `VITE_PUBLIC_PREVIEW` must be absent or false. Content saves then use Django directly and never require another frontend deployment.
5. Create the owner on that server with `docker compose exec app python manage.py createsuperuser`, then test `/owner`, saved company details after restart, logout and password change.
6. Configure the HTTPS email provider and ImageKit server credentials to activate email notifications and media uploads. Saved enquiries remain available when notification configuration is missing or a send outcome is uncertain.

Publishing a static login page does not activate the API. Netlify's static deployment must not be used as an ephemeral SQLite host. Do not introduce a second independent database instance.

## API access

| Route | Access | Purpose |
| --- | --- | --- |
| `GET /api/auth/` | Public | Obtain CSRF token and current session status |
| `POST /api/auth/` | Public, CSRF required, rate limited | Authenticate an active staff account |
| `DELETE /api/auth/` | CSRF required | End the current session |
| `POST /api/password/` | Staff session and CSRF | Validate current password and change it |
| `/api/owner/settings/` | Staff session; CSRF on writes | Persistent company settings, including private recipient |
| `/api/owner/overview/` | Staff session | Actual database counts and integration status |
| `/api/owner/content/` | Staff session; CSRF on writes | Services, projects, publication and attachments |
| `/api/owner/media/` | Staff session; CSRF on writes | Verified ImageKit uploads and guarded deletion |
| `/api/owner/documents/` | Staff session; CSRF on writes | Approved PDF listings |
| `/api/owner/enquiries/` | Staff session; CSRF on writes | Stored enquiries, read status and notification retries |
| `GET /api/public/` | Public | Visible company details and published content only |
| `POST /api/enquire/` | Public, CSRF required, rate limited | Store an enquiry and attempt notification |

Login permits at most 10 attempts per 15 minutes per client IP. Username and password input sizes are bounded. Password whitespace is preserved. Production sessions use HTTP-only, Secure, SameSite=Lax cookies; no browser storage token is used. Login rotates the session and CSRF token. Logout invalidates the stored session. A password change keeps the current session and invalidates other sessions when they next authenticate.

## Recovery

There is no public registration or default password. The login page's help control explains recovery. After independently verifying the owner's identity, an authorised server administrator runs:

```bash
docker compose exec app python manage.py changepassword OWNER_USERNAME
```

The command prompts privately for the new password. Never put passwords on the command line, in source code, or in public company settings.

## Verification

The current test results are recorded in VERIFICATION.md, covering CSRF enforcement, staff-only permissions, session rotation and database persistence across fresh clients, invalid credentials, bounded inputs, preserved password whitespace, rate limiting, logout, password validation and other-session invalidation. The existing company/content/enquiry/media tests also pass. Email and ImageKit tests use mocks; live providers and production server persistence still require activation checks.
