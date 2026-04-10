from django.urls import path
import base.views as views

urlpatterns = [
    path('', views.home, name='home'),
    path('careers/', views.careers, name='careers'),
    path('about/', views.about, name='about'),
    path('login/', views.login, name='login'),
    path('application/continue/', views.application_continue, name='application_continue'),
    path('logout/', views.logout_view, name='logout'),
    path('candidates/details/<int:id>/', views.details, name='details'),
    path('forgotpw/', views.forgotpw, name='forgotpw'),
    path('application/<int:position_id>/<int:page>/', views.application, name='application'),
    path('submit_application/', views.submit_application, name='submit_application'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('company_dashboard/', views.company_dashboard, name='company_dashboard'),
    path('dashboard/questions/', views.question_manager, name='question_manager'),
    path('dashboard/questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('dashboard/questions/<int:question_id>/archive/', views.archive_question, name='archive_question'),
    path('dashboard/positions/add/', views.add_position, name='add_position'),
    path('dashboard/positions/<int:id>/edit/', views.edit_position, name='edit_position'),
    path('dashboard/positions/<int:position_id>/questions/', views.question_manager, name='position_questions'),
    path('dashboard/submissions/<int:id>/', views.submission_detail, name='submission_detail'),
    # Make sure to test all enumeration attacks and edge cases, so I don't completely embarass myself
]
