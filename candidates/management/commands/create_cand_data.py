# This file allows you to create sample candidate data
# Simply run the command: python manage.py create_cand_data

from django.contrib.auth.models import User
from candidates.models import Cand
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
                "linkedin_url": "https://www.linkedin.com/in/johndoe",
                "resume_url": "https://www.example.com/resumes/johndoe.pdf",
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@example.com",
                "linkedin_url": "https://www.linkedin.com/in/janesmith",
                "resume_url": "https://www.example.com/resumes/janesmith.pdf",
            }
        ]

        for cand_data in candidates:
            user = User.objects.create(
                first_name=cand_data["first_name"],
                last_name=cand_data["last_name"],
                email=cand_data["email"],
            )
            Cand.objects.create(
                user=user,
                phone=cand_data["phone"],
                linkedin_url=f"https://www.linkedin.com/in/{cand_data['username']}",
                resume_url=f"https://www.example.com/resumes/{cand_data['username']}.pdf",
            )

        self.stdout.write(self.style.SUCCESS('Successfully created sample candidate data'))