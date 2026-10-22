"""Plain-text Django notification backend using Resend's HTTPS API."""
import hashlib
import json
import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class NotificationRejected(Exception):
    """Provider explicitly rejected the message before acceptance."""


def email_is_configured():
    if not settings.DEFAULT_FROM_EMAIL:
        return False
    if settings.EMAIL_BACKEND == 'core.email_backend.ResendEmailBackend':
        return bool(settings.RESEND_API_KEY)
    if settings.EMAIL_BACKEND.endswith('smtp.EmailBackend'):
        return bool(settings.EMAIL_HOST)
    return True


class ResendEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages or []:
            try:
                if not email_is_configured():
                    raise NotificationRejected('Server email configuration is missing.')
                if not message.recipients():
                    continue
                if message.attachments:
                    raise NotificationRejected('This notification backend supports text messages only.')
                message.message()  # Django validates headers before an external request.
                payload = {'from':message.from_email, 'to':message.to, 'subject':message.subject,
                           'text':message.body, 'reply_to':message.reply_to}
                if message.cc: payload['cc'] = message.cc
                if message.bcc: payload['bcc'] = message.bcc
                if message.extra_headers.get('Message-ID'):
                    payload['headers'] = {'Message-ID':message.extra_headers['Message-ID']}
                digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
                response = requests.post('https://api.resend.com/emails', json=payload,
                    headers={'Authorization':'Bearer '+settings.RESEND_API_KEY,
                             'Idempotency-Key':'estmajo-'+digest},
                    timeout=(5, 20), allow_redirects=False)
                if 400 <= response.status_code < 500:
                    raise NotificationRejected('Email provider rejected the notification. Check provider configuration or quota before retrying.')
                if not 200 <= response.status_code < 300:
                    raise RuntimeError('Email acceptance could not be confirmed.')
                result = response.json()
                if not isinstance(result.get('id'), str) or not result['id']:
                    raise RuntimeError('Email provider did not acknowledge acceptance.')
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent
