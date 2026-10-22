# Architecture and API

The public React app and React owner dashboard stay on the existing Netlify website. Its Edge Function proxies signed `/api/*` requests to Django on Render Free. Neon PostgreSQL stores company content, users, sessions, enquiries and asset references. ImageKit stores uploaded file bytes. The hosted database was changed from SQLite with the owner's approval to avoid paid Render disks. Local development and the legacy Caddy/Docker deployment may still use SQLite.

Resend's HTTPS transport supports notifications on Render Free, where standard SMTP is blocked. A provider-approved sender/API key is required. First-owner setup uses private environment values exactly once; it never resets an existing administrator. See RENDER.md.

Company settings use one singleton `Company` row with a nested JSON document validated by explicit DRF serializers. The private enquiry recipient is a separate model column, never included in the public projection. Repeatable entries support labels, order and visibility. Asset selections are validated against existing uploaded images. The API discards undeclared company fields; JavaScript/HTML is never executed from settings. React displays prose as escaped text rather than injecting HTML.

Services and projects share the Content model. Ordered attachments use an explicit relational model with protected media references and a single-cover validation rule. Documents have separate public/profile flags. Media deletion checks all company image fields, content references, document references and gallery selection. A database-level protected foreign key also prevents deleting attached media.

## Endpoints

| Endpoint | Method | Access / purpose |
|---|---|---|
| `/api/auth/` | GET | Obtain CSRF token and current session state |
| `/api/auth/` | POST | CSRF-protected, rate-limited staff login |
| `/api/auth/` | DELETE | Session logout |
| `/api/password/` | POST | Staff password change with current-password validation |
| `/api/public/` | GET | Published content and allowlisted visible settings only; no-store |
| `/api/enquire/` | POST | CSRF-protected, validated, rate-limited enquiry with UUID idempotency |
| `/api/documents/{id}/download/` | GET | Stream an approved public PDF as an attachment; staff may access private documents |
| `/api/owner/settings/` | GET, PUT | Staff company settings including private recipient |
| `/api/owner/overview/` | GET | Staff actual database counts and configuration state |
| `/api/owner/content/` | GET, POST | Staff services/projects |
| `/api/owner/content/{id}/` | GET, PUT, PATCH, DELETE | Staff content operations |
| `/api/owner/media/` | GET, POST multipart | Staff media library/upload with server metadata verification |
| `/api/owner/media/{id}/` | GET, PATCH, DELETE | Staff media details / guarded remote deletion |
| `/api/owner/documents/` | GET, POST | Staff PDF document management |
| `/api/owner/documents/{id}/` | GET, PUT, PATCH, DELETE | Staff document operations |
| `/api/owner/enquiries/` | GET | Staff enquiry list |
| `/api/owner/enquiries/{id}/` | GET | Staff enquiry details |
| `/api/owner/enquiries/{id}/mark_read/` | POST | Staff mark-read action |
| `/api/owner/enquiries/{id}/retry/` | POST | Staff notification retry with ambiguity confirmation |

The API uses session authentication rather than frontend bearer secrets. The frontend sends `credentials: same-origin` and a CSRF header on writes. Unknown optional content remains empty; missing contacts are hidden. No localStorage/sessionStorage is used as a database. Saved settings trigger a public-data refresh; focus and interval refreshes keep open pages current.

## Operational limits

- Render Free is configured as one instance with external PostgreSQL. SQLite is supported only for local development and the legacy single-instance Docker deployment.
- Images use signed 480/960/1600-pixel transformations and browser srcsets. Videos use native accessible player controls. Video descriptions/transcripts are author-provided; timed-caption track upload and automated caption generation are not included.
- Provider acceptance and actual inbox delivery are different. Delivery/bounce webhooks are not implemented. Unknown provider outcomes require provider-log review before manual retry.
- Public document downloads stream through Django and use an attachment response. Signed media links expire within one hour. Already issued links may work until expiry after unpublishing.
- Search/social metadata is updated in the React document head. Search or social crawlers that do not execute JavaScript may see only the initial static page metadata. Server-rendered social previews are not included in this Vite SPA.
- Throttling uses persistent database counters by reverse-proxy client IP and fixed time windows. Set the proxy trust boundary correctly. It is a practical small-business spam control, not a full external bot-mitigation service.
- Content/settings saves use normal last-write-wins behaviour. For concurrent editing, coordinate saves to avoid one editor overwriting another’s recent changes.
- There is no public password-reset email flow; documented server recovery is provided. No passwords, ImageKit keys or SMTP credentials are placed in public settings.
- There is no Django admin UI dependency: owner workflows are in React.

## Provider references

- [ImageKit Python SDK](https://imagekit.io/docs/integration/python)
- [ImageKit API key authentication](https://imagekit.io/docs/api-keys)
- [ImageKit private files and signed URLs](https://imagekit.io/docs/media-delivery-basic-security)
- [Django 5.2 deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)

These references informed the integration. Actual provider credentials and real-media acceptance still need activation testing.


## Netlify hosting option

The included `netlify.toml` hosts the Vite frontend and a narrowly scoped edge proxy for `/api/*`. Django runs externally on Render with persistent PostgreSQL on Neon. The proxy signs the edge-verified client IP, timestamp, method and API path with a backend-only shared secret; Django rejects invalid/expired signatures before authenticated API handling. Cookie and CSRF protections remain in place. See NETLIFY.md for environment configuration, timeout limits, live connectivity checks and publication prerequisites.
