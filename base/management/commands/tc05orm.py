from django.core.management.base import BaseCommand
from base.models import Candidate, Submission


class Command(BaseCommand):
    help = "TC05 — Validate Cascade Delete Behavior (ORM)"

    def handle(self, *args, **options):
        candidate = Candidate.objects.create(
            email="cascade@test.com",
            first_name="Cascade",
            last_name="Test",
            phone="555-0000",
        )
        submission = Submission.objects.create(candidate=candidate)
        submission_id = submission.id

        candidate.delete()

        if Submission.objects.filter(id=submission_id).exists():
            self.stdout.write(self.style.ERROR("FAIL — submission was not cascade-deleted"))
        else:
            self.stdout.write(self.style.SUCCESS("PASS — submission was cascade-deleted with candidate"))
