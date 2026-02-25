# This file allows you to create sample staff (CompanyStaff) data
# Simply run the command: python manage.py create_staff

from django.contrib.auth.models import User
from base.models import Company, CompanyStaff
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Create sample staff (CompanyStaff) data'

    def handle(self, *args, **kwargs):
        # Create or get a sample company
        company, _ = Company.objects.get_or_create(
            slug="sample-company",
            defaults={"name": "Sample Company"}
        )

        staff_members = [
            {
                "first_name": "Alice",
                "last_name": "Admin",
                "email": "alice.admin@example.com",
                "is_admin": True,
                "password": "adminpass123",
            },
            {
                "first_name": "Bob",
                "last_name": "Staff",
                "email": "bob.staff@example.com",
                "is_admin": False,
                "password": "staffpass123",
            }
        ]

        for staff_data in staff_members:
            user, created = User.objects.get_or_create(
                username=staff_data["email"],
                defaults={
                    "first_name": staff_data["first_name"],
                    "last_name": staff_data["last_name"],
                    "email": staff_data["email"]
                }
            )
            if created:
                user.set_password(staff_data["password"])
                user.save()
            CompanyStaff.objects.get_or_create(
                user=user,
                company=company,
                defaults={"is_admin": staff_data["is_admin"]}
            )

        self.stdout.write(self.style.SUCCESS('Successfully created sample staff data'))
