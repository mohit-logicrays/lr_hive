import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from user.models import EmailTemplate


class Command(BaseCommand):
    help = "Loads default email HTML templates from user/fixtures/email_templates.json"

    def handle(self, *args, **kwargs):
        fixture_path = os.path.join(
            settings.BASE_DIR, "user", "fixtures", "email_templates.json"
        )

        if not os.path.exists(fixture_path):
            self.stdout.write(
                self.style.ERROR(f"Fixture file not found at {fixture_path}")
            )
            return

        with open(fixture_path, "r", encoding="utf-8") as file:
            templates_data = json.load(file)

        created_count = 0
        updated_count = 0

        for item in templates_data:
            fields = item.get("fields", {})
            email_type = fields.get("email_type")

            if not email_type:
                continue

            template, created = EmailTemplate.objects.update_or_create(
                email_type=email_type,
                defaults={
                    "title": fields.get("title", f"{email_type} Template"),
                    "subject": fields.get("subject", ""),
                    "body": fields.get("body", ""),
                    "is_html": fields.get("is_html", True),
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully loaded email templates. Created: {created_count}, Updated: {updated_count}"
            )
        )
