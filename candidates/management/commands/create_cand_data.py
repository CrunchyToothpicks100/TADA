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
                "username": "johndoe",
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "address": "123 Main St, City, Country",
                "likes_guns": True,
                "likes_cars": False,
                "likes_games": True,
                "fruit_preference": "Apple",
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "username": "janesmith",
                "email": "jane.smith@example.com",
                "phone": "+1987654321",
                "address": "456 Oak Ave, City, Country",
                "likes_guns": False,
                "likes_cars": True,
                "likes_games": False,
                "fruit_preference": "Banana",
            }
        ]

        for cand_data in candidates:
            user = User.objects.create(
                username=cand_data["username"],  # or another unique value
                first_name=cand_data["first_name"],
                last_name=cand_data["last_name"],
                email=cand_data["email"],
            )
            Cand.objects.create(
                user=user,
                phone=cand_data["phone"],
                likes_guns=cand_data["likes_guns"],
                likes_cars=cand_data["likes_cars"],
                likes_games=cand_data["likes_games"],
                fruit_preference=cand_data["fruit_preference"],
            )

        self.stdout.write(self.style.SUCCESS('Successfully created sample candidate data'))