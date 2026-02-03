from django.urls import path
from . import views

urlpatterns = [
    path('', views.main, name='main'),
    path('about/', views.about, name='about'),
    path('candidates/', views.candidates, name='candidates'),
    path('candidates/details/<int:id>/', views.details, name='details'),
    path('fruit/', views.fruit, name='fruit'),
]