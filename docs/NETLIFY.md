# Netlify publication

The source includes a Netlify build configuration, SPA route handling and an edge API proxy. **Django runs on Render Free and its persistent PostgreSQL database runs on Neon.** Netlify hosts the React frontend and the API forwarding function; the database is never written to Netlify build directories or transient function storage.

## Current access requirements

Netlify sign-in was completed successfully, and the explicitly labelled public design preview is published at https://estmajo-engineering-solutions.netlify.app/ . See PUBLIC_PREVIEW.md for the observed result and preview behaviour.

Render deployment, Neon access, ImageKit credentials and HTTPS email-provider credentials remain pending. Therefore the full CMS, stored enquiries, uploads and automatic email delivery are not yet active. The complete production build remains gated on backend connectivity and signature verification.

## 1. Activate the backend

Use RENDER.md for the approved Render Free + Neon PostgreSQL deployment. No paid Render disk is needed. Keep database contents and sessions in Neon, media in ImageKit and secrets in hosting environment settings. Create the initial owner using the private one-time bootstrap procedure because Render Free has no shell. The legacy Docker/SQLite option remains documented separately in DEPLOYMENT.md.

Set `ALLOWED_HOSTS` to the real backend hostname and include both your Netlify HTTPS origin and the backend origin in `CSRF_TRUSTED_ORIGINS`. Keep `DEBUG=false`, Secure HTTP-only session cookies and CSRF protection enabled. Do not add wildcard trusted origins. Domain-less Django cookies are forwarded by the edge proxy and stay scoped to the public Netlify hostname.

Generate a cryptographically random proxy secret with at least 32 characters. Store the same value as `NETLIFY_PROXY_SECRET` in the backend and in Netlify. Do not expose it with any `VITE_` prefix, put it in public company fields or commit it. When enabled, the backend requires a valid signed proxy request for every `/api/` call; direct unsigned API calls return 403. Local management commands can use a private Neon direct connection for recovery and backups.

The signature binds the timestamp, edge-verified client IP, HTTP method and path. The backend rejects invalid/expired signatures and uses the verified IP for per-client rate limits, rather than treating all Netlify visitors as one client. Normal session authentication and CSRF protection still apply after proxy verification.

## 2. Configure Netlify

Connect the source repository or deploy this source using Netlify CLI. Use the project root containing `netlify.toml`; the build output directory is `frontend/dist`.

Set these environment variables through Netlify’s secure settings with build **and** runtime/edge availability:

| Variable | Value |
|---|---|
| `DJANGO_API_ORIGIN` | The actual backend HTTPS origin, without `/api/` or another path |
| `NETLIFY_PROXY_SECRET` | The same secret configured on Django |

These must be set in the Netlify dashboard/CLI environment settings, not in the checked-in `netlify.toml`; runtime edge functions cannot read variables declared only in that file.

The build intentionally fails if these required values are missing. It also sends a signed connectivity probe to the live Django public API and requires a successful verification header, so an absent backend or mismatched secret blocks publication. It never substitutes a fake database, browser storage, mock enquiries or success messages.

The included API edge function is at `netlify/edge-functions/django-api.ts`. It streams request bodies upstream, forwards Cookie and CSRF headers, preserves backend Set-Cookie responses, disables API caching and returns useful 502/503 errors if the backend is unavailable. The public source package contains no credentials.

**Do not use Netlify Drop with only the raw frontend `dist` folder for this full application.** It would omit the edge function and server connectivity. Deploy the complete source using the root configuration.

## 3. Email and media activation

Set ImageKit keys and SMTP credentials only on Django, then send an actual website enquiry and upload image, video and PDF samples. `estmajo@hotmail.com` is already the public email and separate notification recipient; it is not automatically a configured authenticated sender.

Netlify Edge Functions have a documented response-header timeout. Large image/video uploads or slow provider checks can exceed that limit even though the original single-server deployment allows longer requests. Test representative file sizes and reduce configured upload limits if necessary. The upload UI reports failures, and the media audit command identifies uploads left orphaned by interrupted requests. Do not claim the full 100 MB video limit works through Netlify until a live test confirms it within your plan’s limits.

## 4. Publish and verify

After signing into the correct Netlify account/team, publish the configured source. Record the actual deployment URL returned by Netlify; never invent a `.netlify.app` hostname.

Verify on that URL:

- All public routes, original logo, both phone links, email link and contact address.
- Owner login, Secure/HTTP-only sessions, CSRF rejection, logout and password change.
- Saved company changes appearing without a frontend rebuild.
- An enquiry saved in SQLite, accepted by the email provider and received by the company.
- Private settings/drafts remaining inaccessible to logged-out visitors.
- Image/video/PDF upload, playback and public PDF download.
- Per-client rate limiting through signed proxy requests.
- Mobile navigation, keyboard accessibility and copy-number behaviour.
- Persistence after backend restart and an exported backup/restore drill.

Only after these checks should the Netlify page be described as fully active.

## Local checks included

```bash
node --test deploy/netlify-proxy.test.mjs
npm --prefix frontend run build
DEBUG=true SECRET_KEY=local-testing-only-key-at-least-32-characters .venv/bin/python backend/manage.py test core
```

The proxy tests use mocked HTTP responses and confirm forwarding, request signing, Set-Cookie preservation and error handling. They do not establish Netlify deployment or live provider connectivity.

Official references: [Netlify Edge Functions API](https://docs.netlify.com/build/edge-functions/api/), [runtime environment variables](https://docs.netlify.com/build/edge-functions/environment-variables/), [Edge Function limits](https://docs.netlify.com/build/edge-functions/limits/).
