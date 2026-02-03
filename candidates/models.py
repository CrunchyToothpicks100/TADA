from django.contrib.auth.models import User
from django.db import models

class Cand(models.Model):
    # Default fields from User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Extra fields
    phone = models.CharField(max_length=20, blank=True)
    likes_guns = models.BooleanField(default=False)
    likes_cars = models.BooleanField(default=False)
    likes_games = models.BooleanField(default=False)
    fruit_preference = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.user.username
