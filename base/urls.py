from django.urls import path
import base.views as views

urlpatterns = [
    path('', views.main, name='main'),
    path('about/', views.about, name='about'),
    path('candidates/', views.candidates, name='candidates'),
    path('candidates/details/<int:id>/', views.details, name='details'),
    path('login/', views.login, name='login'),
    path('forgotpw/', views.forgotpw, name='forgotpw'),
    path('application/', views.application, name='application'),
    path('submit_application/', views.submit_application, name='submit_application'),
    path('home/', views.home, name='home'),
]