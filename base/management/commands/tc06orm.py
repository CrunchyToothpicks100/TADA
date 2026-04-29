from django.core.management.base import BaseCommand
from django.db.models.deletion import ProtectedError
from base.models import Position


class Command(BaseCommand):
    help = "TC06 — Validate PROTECT on Position (ORM)"

    def handle(self, *args, **options):
        try:
            position = Position.objects.get(
                title="Backend Engineer",
                company__slug="acme-corp",
            )
        except Position.DoesNotExist:
            self.stdout.write(self.style.ERROR("SKIP — no 'Backend Engineer' position at 'acme-corp' found"))
            return

        try:
            position.delete()
            self.stdout.write(self.style.ERROR("FAIL — position was deleted; PROTECT did not fire"))
        except ProtectedError:
            self.stdout.write(self.style.SUCCESS("PASS — ProtectedError raised, position deletion blocked"))
