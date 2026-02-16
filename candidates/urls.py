from django.urls import path
from .views import views
from .views import auth_views

urlpatterns = [
    path('', views.main, name='main'),
    path('about/', views.about, name='about'),
    path('candidates/', views.candidates, name='candidates'),
    path('candidates/details/<int:id>/', views.details, name='details'),
    path('login/', auth_views.login, name='login'),
    path('signup/', auth_views.signup, name='signup'),
    path('forgotpw/', auth_views.forgotpw, name='forgotpw'),
    path('application/', views.application, name='application'),
    path('submit_application/', views.submit_application, name='submit_application'),
]