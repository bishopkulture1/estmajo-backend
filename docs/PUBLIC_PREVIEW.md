# Published public preview

**Verified published page:** https://estmajo-engineering-solutions.netlify.app/

The public design preview was published on Netlify on 21 October 2026. It displays the original ESTMAJO logo, seven service categories, Warri office address, RC 7810123, public email and the two confirmed telephone numbers. The discarded telephone number is not included.

## What works on the published preview

- Public page navigation and individual service routes, including a direct route reload.
- Original logo display without changing its lettering or proportions.
- Telephone links for +2348123834601 and +2347065938360.
- Public email links to estmajo@hotmail.com.
- Contact fields, service selection and an **Open email draft** action.
- Copy-number control; the main number was copied successfully in browser testing.
- A branded administrator login page with password visibility and recovery guidance. Credential entry is disabled until Django is connected.

The homepage, an individual HVAC service route, contact details and owner notice were checked in the published browser page. Rendered images reported no broken image loads. The deployed form opens an email draft; no message is sent automatically, no online enquiry record is created in this preview, and an actual email was not sent during verification. Live mobile-device testing and the complete Django application still require activation checks.

## What still needs backend activation

The preview is clearly labelled **PUBLIC WEBSITE PREVIEW**. It does not provide active CMS authentication, persistent content editing, enquiry storage/tracking, ImageKit uploads or automatic email notifications. Those features are implemented in the full Django application but require the Render Free + Neon backend and private integration settings described in RENDER.md.

The preview uses only an approved public snapshot from `deploy/company-preview.json`. It does not use browser storage as a database and never claims a save or email delivery happened. The normal production build uses authenticated Django APIs instead. The snapshot is copied only into the separately generated preview output, not into the regular production frontend.

## Rebuild this preview

```bash
npm --prefix frontend ci
node deploy/public-preview.mjs
```

This creates the separately labelled frontend-only output in `netlify-public-preview/`. It is suitable for a static Netlify Drop upload. Do not treat it as the full CMS deployment. For the complete application, deploy the full source using the root `netlify.toml`, a live Django origin, matching proxy secret, PostgreSQL, HTTPS email and ImageKit configuration.

PDF exports are reading copies of the source folders. Use the source ZIP and code files to run or deploy the application.


## Updated administrator page

The owner route is https://estmajo-engineering-solutions.netlify.app/owner . The branded login page was published and checked in the browser on 21 October 2026. The original company logo, administrator fields, backend activation status and expandable recovery help were present. Credential fields remain intentionally disabled in the static preview. The full application enables them only after a successful Django session handshake. See ADMIN_SETUP.md.
