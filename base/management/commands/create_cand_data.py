# This file allows you to create sample candidate data
# Simply run the command: python manage.py create_cand_data

from django.contrib.auth.models import User
from base.models import Candidate
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create sample candidate data'

    def handle(self, *args, **kwargs):
        # Create sample candidate data
        candidates = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "555-1234",
                "linkedin_url": "https://www.linkedin.com/in/johndoe",
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com",
                "phone": "555-5678",
                "linkedin_url": "https://www.linkedin.com/in/janesmith",
            }
        ]

        for cand_data in candidates:
            user = User.objects.create(
                username=cand_data["email"],
                first_name=cand_data["first_name"],
                last_name=cand_data["last_name"],
                email=cand_data["email"],
            )
            Candidate.objects.create(
                user=user,
                email=cand_data["email"],
                first_name=cand_data["first_name"],
                last_name=cand_data["last_name"],
                phone=cand_data["phone"],
                linkedin_url=cand_data["linkedin_url"],
            )

        self.stdout.write(self.style.SUCCESS('Successfully created sample candidate data'))