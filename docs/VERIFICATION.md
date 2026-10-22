# Verification summary — 21 October 2026

## Implemented outcome

A React public website and React owner workspace backed by authenticated Django APIs, PostgreSQL hosted content storage (SQLite local compatibility), ImageKit integration code, enquiry storage and email notification tracking. The owner can add company/contact details after initial setup without editing source code or rebuilding the website.

**The public design preview is published at https://estmajo-engineering-solutions.netlify.app/ .** The full Django application is not activated. No live SMTP inbox delivery, actual ImageKit upload or full-application browser test is claimed. Public-preview browser checks are recorded below.

## Executed checks

| Check | Result | Evidence / scope |
|---|---|---|
| Backend integration/security suite | PASS | 47 tests, `Ran 47 tests … OK` |
| Django system checks under test settings | PASS | `System check identified no issues (0 silenced).` |
| Production deployment checks with HTTPS settings and a generated strong test secret | PASS with one documented warning | Only `security.W021`: HSTS preload is intentionally not enabled; normal HSTS remains enabled |
| TypeScript and production frontend build | PASS | `tsc -b && vite build`; 1,595 modules transformed; Vite build completed |
| Legacy/local SQLite persistence across process restart | PASS | Company setting written in one process, read in a fresh Python process; seven seeded services also preserved |
| Consistent database backup | PASS | SQLite online backup created, `PRAGMA integrity_check` returned `ok` |
| Restored snapshot readable by Django | PASS | Fresh Python process opened the snapshot and retrieved the saved company setting |
| Browser QA | PUBLIC PREVIEW CHECKED; FULL APP PENDING | Published homepage, service route/reload, contact details, number-copy and owner activation notice checked. Full Django and real mobile-device checks remain pending. |
| Docker deployment and HTTPS certificate issuance | NOT VERIFIED | Docker runtime/target hosting access not available for this build session |
| Real SMTP provider and inbox delivery | NOT VERIFIED | SMTP credentials/verified sender not supplied; company recipient is now set to the supplied email |
| Real ImageKit image/video/PDF upload and playback | NOT VERIFIED | ImageKit credentials/account not supplied; upload transport and metadata checks tested with mocked provider responses |
| Original logo integration | IMPLEMENTED | Supplied JPEG bundled byte-for-byte; header, hero and footer use proportionally contained rendering; browser visual QA remains unverified |

The isolated test environment emitted a warning that the local `staticfiles` directory did not yet exist. Production startup includes `collectstatic`. No real company records, administrator credentials, secret environment files or populated database are included in the source archive.

## Automated coverage

1. All owner APIs reject anonymous access.
2. Non-staff accounts cannot use owner APIs.
3. Anonymous login requires CSRF; valid login creates an HTTP-only session cookie.
4. Logout invalidates access; password change verifies the current password and applies validators.
5. Incorrect passwords and inactive accounts are rejected.
6. Empty optional company details can be saved before all information is available.
7. Multiple emails, telephone numbers and offices persist in SQLite.
8. Reordering, hiding and removing contact entries alter the public projection.
9. Private enquiry recipients and hidden email addresses are absent from public API responses.
10. Social profiles require visibility and owner verification before public display.
11. Invalid email, telephone, URL, timezone and duplicate-primary values are rejected.
12. Unknown company fields are excluded; executable URL schemes are rejected.
13. Business-hour validation and time serialization work in the JSON-backed settings document.
14. Service/project create, publish, unpublish and delete work; drafts remain absent from public content.
15. Duplicate attachments/multiple covers are rejected.
16. Private media/documents remain absent from public listings.
17. Settings, gallery and document references block unsafe shared-media deletion.
18. Valid enquiries persist before notification; the sender and Reply-To are distinct.
19. Repeated submission tokens do not duplicate enquiries or successful notifications.
20. Missing notification configuration leaves a saved enquiry with a failed status; later retries reuse the same record.
21. Ambiguous transport failure is tracked as unknown; retry needs explicit duplicate-risk confirmation.
22. Active sending is protected from immediate retries; stale sending can be explicitly retried after five minutes.
23. Honeypot, telephone validation, draft-service rejection, CSRF and rate limiting apply to enquiries.
24. Official SDK generates signed, expiring responsive image URLs.
25. Image/video/PDF upload handlers verify simulated provider metadata before creating media records.
26. Failed metadata checks attempt remote orphan cleanup; unsupported or forged files are rejected.
27. Unused media deletion removes the local record after remote deletion succeeds.
28. Public PDF download enforces visibility and returns an attachment response with streamed bytes.

Several closely related assertions share a single test method; there are 28 executed test methods in total. ImageKit network calls and SMTP are simulated where noted. Native video controls, responsive layouts, keyboard navigation, modal focus trapping and copy-number interactions are implemented but have not been exercised in a real browser in this environment.

## Production activation checklist

- [x] Confirmed **ESTMAJO ENGINEERING SOLUTIONS LTD** from the owner’s supplied details.
- [x] Included the original supplied logo unchanged, with proportional display.
- [ ] Approve the real company profile, contact details, service descriptions and privacy information.
- [ ] Provide a single persistent server, domain/DNS control and HTTPS setup; do not use ephemeral SQLite storage.
- [ ] Configure a long random secret, allowed hosts, CSRF origins, disabled debug and production secure cookies.
- [ ] Create the owner interactively; test login, logout, password change and documented recovery.
- [ ] Configure ImageKit through server environment variables; upload actual image, MP4/WebM video and PDF samples.
- [ ] Verify successful ImageKit metadata/privacy checks, responsive images, video playback, captions/descriptions, replacement and guarded deletion.
- [ ] Verify public company-profile download from the real ImageKit account and private-document rejection.
- [ ] Configure SMTP, authenticated sender and the separate private enquiry recipient.
- [ ] Send a real enquiry; check the dashboard record, provider acceptance and actual receiving inbox.
- [ ] Test a failed notification followed by an authorised retry without a second enquiry record.
- [ ] Add multiple telephone/email/office entries; reorder and hide them; inspect header, footer, contact page and mobile contact bar after saving.
- [ ] Click real mailto, tel, copy-number, WhatsApp and directions links.
- [ ] Publish/unpublish an actual project and verify a logged-out browser cannot retrieve its draft content.
- [ ] Restart the production application and verify company details, content, enquiries and owner access persist.
- [ ] Perform a production backup/export and restore drill; verify ImageKit originals are backed up independently.
- [ ] Check mobile navigation, keyboard focus, screen-reader labels, contrast, links and real-device playback/download behaviour.
- [ ] Review server logs and HTTPS, then announce the verified URL.

## Confirmed branding and contact update

Migration `0003_confirmed_company_details` installs the owner-confirmed legal name, RC number, Warri office, email and two complete telephone numbers. A separate private notification-recipient setting is initialised to the supplied email. Existing company data outside those supplied fields is preserved, and the normal startup seed does not reapply the migration or overwrite later dashboard edits.

Two additional regression tests check the supplied branding/contact projection, exclusion of private recipient fields from public APIs, the bundled-logo visibility control, and preservation of later owner edits by the service seed command. All 26 backend tests and the frontend production build passed after this update. Logo bytes in the source and built output match the supplied JPEG. Public-preview deployment and limited browser checks are now verified; full Django, SMTP and ImageKit activation remain pending.


## Netlify preparation and removal update

The discarded telephone entry is removed from fresh-install data, existing saved settings (through migration 0004), owner interface and documentation. Only the two confirmed telephone numbers remain.

The application now includes Netlify SPA routing, an edge API proxy, a build-time backend connectivity/signature gate, backend signature validation and uncached API responses. Netlify hosts the frontend/proxy; persistent Django hosting remains external. Three local proxy tests passed with mocked upstream responses, including signing, Cookie/CSRF forwarding, multiple Set-Cookie preservation and 502/503 handling. The expanded Django suite contains 28 passing tests. The frontend production build passed.

**Full-application activation blocker:** Netlify sign-in and public-preview publication succeeded, but no live persistent Django origin was supplied. The published preview is not the active CMS. Real proxy deployment, full-application browser behaviour, SMTP delivery and ImageKit uploads still require the activation checks in NETLIFY.md.


## Published preview browser checks

Published URL: https://estmajo-engineering-solutions.netlify.app/

Netlify showed a Published state and the final project name `estmajo-engineering-solutions`. The public URL loaded the ESTMAJO homepage. Browser checks verified a service detail page and direct-route reload, the exact office address, both complete `tel:` numbers, the public email link, the visible Open email draft action, successful copy-number feedback, and the owner activation-pending notice. No broken rendered images were reported. The email draft was not sent during testing. The preview does not simulate CMS saves or enquiry delivery. See PUBLIC_PREVIEW.md for the remaining backend-dependent features.


## Administrator login update — 21 October 2026

The owner placeholder was replaced with a branded React login page. Connected deployments establish a CSRF session before enabling credentials; failed connection states offer a retry. Login keeps the form visible while submitting, clears the password after an attempt, and displays backend errors. Password visibility and recovery guidance are available. Public preview builds show the same design with credential entry disabled and an explicit activation notice.

The backend now validates login input types and lengths without trimming passwords. Three added tests verify input boundaries and whitespace, brute-force rate limiting, session/CSRF rotation, database-backed session reuse by a fresh client, logout invalidation, weak-password rejection and invalidation of other sessions after a password change. All 31 backend tests and the TypeScript/Vite build pass. ADMIN_SETUP.md contains exact local and production activation steps. No production Django host, SMTP or ImageKit activation is claimed.

The updated Netlify deployment `6ad8c3c61b5f2aac54f9e189` reached Published. The exact `/owner` URL loaded the new login design, original logo, activation-required status and disabled credential fields. The help button was expanded and collapsed successfully, displaying the documented recovery process. This verifies the published login design, not a live Django sign-in.


## Render deployment preparation — 21 October 2026

The Render integration is connected, but workspace selection and paid-resource creation have not been confirmed. No Render resources were created and no live Render URL or Netlify backend activation is claimed. A matching GitHub repository was found, but the connected permission is read-only, so source was not pushed there.

Added `render.yaml` for a single Python service with 1 GB persistent disk, controlled manual deployments, exact Render host allowance and a database-readiness endpoint. Build does not migrate production SQLite. Startup verifies the actual Linux mount, database location, write access and required security settings, then applies migrations and seeds before Gunicorn starts.

Executed results: 36 Django tests pass, including five new health/storage guard tests; the Blueprint passes the current official Render JSON Schema; both scripts pass Bash syntax checks; no missing migrations were detected; Django production checks report only the previously documented HSTS-preload warning. Python 3.12.15 is selected for the Render runtime; the hosted runtime build has not yet run. Full deployment, real persistent-disk restart, administrator creation, Netlify proxy connectivity, SMTP, ImageKit and offsite recovery still need hosted verification. See RENDER.md for exact activation steps and proposed costs.


## Approved free-tier architecture — 21 October 2026

The owner approved moving hosted storage from SQLite to PostgreSQL so Render can use its Free plan without a disk. The current Blueprint requests only one Free web service, with no Render disk or Render Postgres resource. Neon is the intended separate persistent database. ImageKit remains the media provider. No paid resources were created.

Implemented PostgreSQL URL parsing with enforced CA/hostname-verified TLS, pooler-compatible cursors/connections, direct migration support, a Render guard that refuses missing PostgreSQL, and a PostgreSQL driver in the lockfile. The persistent rate bucket is row-locked under PostgreSQL. Initial administrator bootstrap uses private environment credentials, validates and hashes the password, serializes setup on the company row, and never replaces an existing administrator.

Implemented Django email transport through Resend HTTPS, preserving the authenticated sender and validated visitor Reply-To. It distinguishes explicit rejection (failed) from ambiguous transport outcomes (unknown), requires a provider email ID before marking accepted and supplies a stable idempotency key. Provider deduplication is time-limited; real delivery remains unverified.

The browser retries only safe public/session reads during free-service wake-up. Writes, uploads and enquiry posts are never automatically retried. The production Netlify build allows bounded wake-up retries with fresh proxy signatures and forces the full application mode. A PostgreSQL backup command keeps credentials out of command arguments, refuses overwrites, restricts file permissions and removes failed partial output. Updated guides cover first admin setup without Render Shell, direct-connection recovery and backups, source transfer, free-plan limitations and integration activation.

Executed checks: **47 Django tests pass using an isolated SQLite test database**, including PostgreSQL configuration contracts, HTTPS email mocks, bootstrap access/password handling and backup-security tests. **Three safe-read tests pass**, covering cold HTML, forbidden responses and bounded 503 retries. The TypeScript/Vite production build passes. The current Blueprint passes Render's official JSON Schema and an explicit assertion of Free/no-disk/no-Render-database. No new model migrations are needed.

**Not verified:** migrations and queries against an actual PostgreSQL server; live Neon TLS/permissions; real Render deployment/restart; initial hosted administrator creation; the live Netlify-to-Render proxy; real SMTP/HTTPS email acceptance or inbox delivery; actual ImageKit image/video/PDF uploads/playback; and PostgreSQL backup/restore against a real database. No live PostgreSQL test database is connected. A matching GitHub repository is still read-only through the current connection, so this source has not been pushed there. The public Netlify preview is unchanged and the full backend is not yet live.


## Neon provisioning result

The Neon connection is confirmed. Read-only account discovery reported the single organisation on its **Free** plan and no existing ESTMAJO project. Created project `estmajo-engineering` (`spring-art-84705068`) in AWS Frankfurt, PostgreSQL 17, with branch `production` (`br-nameless-thunder-bajg3urp`), database `company` and role `estmajo_owner`. A provider-mediated read-only query returned the expected database/role and PostgreSQL 17.11; the table list is empty. Resource identifiers, without credentials, are recorded in deploy/neon-project.json. No paid plan or upgrade was requested.

A direct Django migration attempt could not resolve the Neon PostgreSQL hostname from the execution environment. It failed before applying migrations. This is a network-verification limitation, not proof of a working Django-to-Neon connection. No isolated test branch was created because the direct connection was unavailable; all 47 Django tests remain isolated local SQLite tests. No production administrator was invented or created.

Render reports no workspace selected and explicitly requires the user to identify the intended workspace before scoped operations. GitHub access to the matching existing repository remains read-only. These prevent publishing the prepared source and creating the Render service. Private database URLs were kept in session memory and not written to source, artifacts or logs.

The unused Neon compute endpoint was suspended after verification to conserve free-tier compute until the backend is connected. This preserves the database; live connection/resume behaviour remains to be verified on Render.
