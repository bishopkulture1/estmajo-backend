# ESTMAJO BACKEND — upload to `bishopkulture1/estmajo-backend`

Target branch: `estmajo-backend-update` (create it from `main`). DO NOT upload to the frontend repository.

Extract the ZIP. Upload its **contents** to the branch root: `backend/`, `render.yaml`, `docs/`, `UPLOAD_GUIDE.md`. Preserve the `backend/` folder — this is the Render root directory.

This preserves the existing Django + DRF backend, Neon PostgreSQL integration, ImageKit private-media signed delivery, original single-owner authentication and Resend HTTPS email backend. Added a small media signing regression test. No schema migrations or technology changes.

**Resend is already coded; real delivery requires configuration:** In Render environment, set `EMAIL_BACKEND=core.email_backend.ResendEmailBackend`, `RESEND_API_KEY`, and `DEFAULT_FROM_EMAIL` using a **verified Resend sender/domain**. Also set company enquiry recipient in the owner dashboard. Use Resend Free plan quotas. An API key is not included in this ZIP. Live email delivery cannot be verified without connecting Render and Resend.

**Media playback:** Set `IMAGEKIT_PRIVATE_KEY` and `IMAGEKIT_URL_ENDPOINT` privately on Render. Existing backend creates private uploads and generates signed URLs for display. Signed URLs expire after one hour and must be refreshed for later playback; verify actual upload/download in production.

**Render:** Set repository to `bishopkulture1/estmajo-backend`, branch after review, rootDir `backend`, build `bash bin/render-build.sh`, start `bash bin/render-start.sh`, health `/_health/`. Also maintain Neon `DATABASE_URL`, matching `NETLIFY_PROXY_SECRET`, `SECRET_KEY`, `DEBUG=false`, and trusted origins. Never upload real `.env`, database dumps, or passwords.

No files were pushed to GitHub or deployed; they are prepared for review and manual upload. Test `python backend/manage.py test core` with project dependencies before merging into `main`.
