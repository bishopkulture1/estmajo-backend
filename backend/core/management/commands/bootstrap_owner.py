"""One-time initial owner setup for hosting without an interactive shell."""
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Company


class Command(BaseCommand):
    help = 'Create the first owner from private BOOTSTRAP_ADMIN_* environment values. Never resets existing accounts.'

    def handle(self, *args, **options):
        User = get_user_model()
        with transaction.atomic():
            # The singleton exists after migrations. Lock it for first-owner serialization.
            Company.objects.select_for_update().get(pk=1)
            if User.objects.filter(is_staff=True).exists() or User.objects.filter(is_superuser=True).exists():
                return
            username = os.getenv('BOOTSTRAP_ADMIN_USERNAME', '').strip()
            password = os.getenv('BOOTSTRAP_ADMIN_PASSWORD', '')
            email = os.getenv('BOOTSTRAP_ADMIN_EMAIL', '').strip()
            if not username and not password and not email:
                self.stdout.write('No initial owner configured. Set private BOOTSTRAP_ADMIN_* environment values to activate owner access.')
                return
            if not username or not password:
                raise CommandError('Initial owner username and password must both be configured privately.')
            user = User(username=username, email=email, is_staff=True, is_superuser=True, is_active=True)
            try:
                if len(password) < 12:
                    raise ValidationError('Password must contain at least 12 characters.')
                validate_password(password, user)
                user.set_password(password)
                user.full_clean()
                user.save()
            except ValidationError:
                # Neither supplied credentials nor provider/database exception details are logged.
                raise CommandError('Initial owner details failed validation. Use a unique valid username, valid optional email and a strong password of at least 12 characters.') from None
        self.stdout.write('Initial owner created. Remove BOOTSTRAP_ADMIN_PASSWORD from hosting configuration after verification.')
