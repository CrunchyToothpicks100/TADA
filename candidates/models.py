from django.contrib.auth.models import User
from django.db import models

class Cand(models.Model):
    # Default fields from User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    linkedin_url = models.URLField(blank=True)
    resume_url = models.URLField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email
