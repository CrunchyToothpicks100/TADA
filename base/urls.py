from django.urls import path
import base.views as views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('candidates/', views.candidates, name='candidates'),
    path('candidates/details/<int:id>/', views.details, name='details'),
    path('forgotpw/', views.forgotpw, name='forgotpw'),
    path('application/', views.application, name='application'),
    path('submit_application/', views.submit_application, name='submit_application'),
    path('candidate_dashboard/', views.candidate_dashboard, name='candidate_dashboard'),
    path('staff_dashboard/', views.staff_dashboard, name='staff_dashboard'),
    # path('staff_dashboard/candidates/', views.staff_candidates, name='staff_candidates'),
    # path('staff_dashboard/candidates/<int:id>/', views.staff_candidate_details, name='staff_candidate_details'),
    path('staff_dashboard/positions/<int:id>/edit/', views.edit_position, name='edit_position'),
]