from django.urls import path
from .views import home


# Regular urls

urlpatterns = [
    path("", home, name="home"),
]

