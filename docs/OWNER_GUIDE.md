# Owner’s guide

## Sign in

Open your website followed by `/owner`. When the company server is connected, enter the owner username and password, and sign in. Use **View website** to open the public site in another tab. Sign out when finished, especially on a shared device.

## Add company details after launch

Select **Company Information & Contact Settings**. All details may be completed later; unknown optional fields should remain empty.

1. In **Company identity**, the confirmed ESTMAJO name and supplied logo are ready. To replace the original logo, upload a replacement in the media library and select it. To hide the bundled logo when no replacement is selected, untick **Use original supplied logo when no replacement is selected**. Logos retain their natural proportions. Favicon selection remains optional.
2. In **Company profile**, add the introduction, description, mission, vision, values and optional year established. Publish only facts approved by the company.
3. In **Email addresses**, add the main public email. The **Private enquiry recipient** receives website notifications and is never returned by the public API. It does not have to match the public address.
4. Under **Additional email addresses**, **Telephone numbers**, **Office addresses**, **Online presence** and **Additional Company Details**, choose **Add entry**. Give each entry a useful label such as Sales or Main office. Use the arrow buttons to reorder entries. Use **Show publicly** to hide details. Use the remove button to remove an entry, then save.
5. Enter telephone/WhatsApp numbers in international format: `+`, country code and national number without the national leading zero. Extensions are optional. Choose one primary telephone number for the footer and mobile call button. Country codes are included in the validated number itself.
6. Add main office and branch addresses as separate entries. The first visible office appears first. Map and directions links must be complete HTTP/HTTPS links. Social profiles appear only if you confirm they are official and visible.
7. Set each known day’s hours with **Set hours**, select Closed or enter opening/closing times, and set an IANA timezone such as Africa/Lagos. Leave days unset when unknown. Add a holiday notice if needed.
8. Add the leadership name, position, photo, biography and message. The separate **CEO / Leadership** menu edits the same saved fields.
9. Complete footer, search/sharing information and approved privacy text. Sharing images and favicons must be uploaded images. Additional details support plain text and validated links, not scripts or executable HTML.
10. Choose **Preview** to review unsaved information. Choose **Save Changes** to publish the saved settings. **Cancel Unsaved Changes** restores the last saved values. The dashboard warns before leaving an edited form.

Saving updates the server database. The public website uses the new details without rebuilding or redeploying. Refresh an already open public tab or switch back to it to fetch the latest data. Missing contact details hide the corresponding call/email/WhatsApp/directions controls.

## Services and projects

Open **Services** or **Projects**, choose **Add**, then enter the title, unique URL slug, summary and full description. Keep the slug lowercase with hyphens. Lower display-order numbers appear first; the list arrows also reorder entries.

Use the media selector to attach photographs/videos already uploaded to the media library. Add alternative text or a video description, a useful caption/transcript and an order number for each attachment. Select only one image as the cover. Remove attachment detaches it without deleting the underlying media file.

Use **Preview** to review a draft. Tick **Published on the website** and save to make the content public. Untick and save to unpublish. Draft pages and media are excluded from public APIs; previously issued signed asset links expire within one hour. Delete asks for confirmation and removes the content record. The seven supplied service category names are preloaded without invented technical claims.

## Upload images, videos and PDF documents

Open **Media library**, choose **Upload file**, and select a supported file. Watch the progress bar; server verification runs after transfer reaches 100%. Uploads need ImageKit configuration on the server. Errors explain what to correct. Do not repeatedly upload a timed-out file without checking whether it already appears in the library.

Choose **Edit details** to add alternative text, a caption, display order or gallery visibility. Making a file visible in the gallery is a separate publication decision. Uploading alone does not publish it.

To replace a file: upload the replacement; change the relevant company image, project/service attachment or document to the replacement; save; then delete the old unused file. The backend blocks permanent deletion of files referenced by settings, content, documents or the gallery. Turn off gallery visibility before deleting an otherwise unused gallery image. The Unused filter helps find unattached files.

## Company profile and public documents

Upload an approved PDF in the media library. Open **Company documents**, choose **Add company document**, enter its title and choose the PDF. Mark **Approved for public download** when ready. Mark **Company profile document** for the profile link in the footer. Other public documents appear on the About page. Set display order and save.

Removing a document listing does not delete its uploaded PDF. Keep unapproved documents private. Do not upload confidential company records intended to stay outside the website system.

## Enquiries

The overview shows real counts. Open **Enquiries** and choose a record to read it, mark it read and reply using your email application. Filter for unread enquiries or notification issues.

- **pending:** saved and waiting for a send attempt.
- **sending:** a notification attempt is underway or was interrupted.
- **accepted:** the email provider accepted the notification; inbox delivery is not proven by this status.
- **failed:** required recipient/server configuration is missing. The enquiry is still saved.
- **unknown:** the notification’s outcome could not be confirmed. Check your provider before retrying.

After correcting configuration, use **Retry notification**. For an unknown/stale sending result, the dashboard warns that a retry might duplicate a notification. Sending records cannot be retried during the first five minutes. Retrying never creates a second enquiry record. Your server administrator can investigate delivery/bounce logs with your email provider.

## Password and recovery

The login page has a password visibility control and **Need help signing in?** guidance. If it says **Backend activation required**, server setup must be completed before signing in; no default password is supplied. See ADMIN_SETUP.md.

Use **Account settings** to change the password. Enter the current password and confirm the new strong password. If you forget it, contact the authorised server administrator, who must verify your identity and use the interactive Django `changepassword` command. On Render Free, the administrator runs this locally with a securely configured direct Neon connection; an interactive Render shell is not required. Initial bootstrap cannot reset an existing account. There is no public “reset password” email flow in this release.

## Before announcing launch

Review the confirmed ESTMAJO branding and Warri details, approve the visible company information, test the public call/email/WhatsApp/directions links, send a real enquiry, verify its arrival with the company, and check uploads and downloads. Your server administrator should verify backups and persistence after restarting the application.

## Company details included in this version

- **Name:** ESTMAJO ENGINEERING SOLUTIONS LTD
- **Registration:** RC 7810123
- **Office:** D5 Edewor Estate, Opposite Shafa Filling Station, By Enerhen Motel, Warri, Delta State, Nigeria
- **Public email and separate notification recipient:** estmajo@hotmail.com
- **Main telephone:** +234 812 383 4601
- **Additional telephone:** +234 706 593 8360

Only the two confirmed telephone numbers are included. No WhatsApp number or business hours have been assumed.

The original supplied logo is a bundled brand asset, so it is available before ImageKit activation. Future uploaded replacement images/videos/documents continue to use ImageKit. Company settings can switch off this bundled fallback or choose a new uploaded logo at any time.
