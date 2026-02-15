from django.http import HttpResponse
from django.template import loader

from candidates.models import Cand, User


def login(request):
    template = loader.get_template('auth/login.html')
    return HttpResponse(template.render())

def signup(request):
    template = loader.get_template('auth/signup.html')
    return HttpResponse(template.render())

def forgotpw(request):
    template = loader.get_template('auth/forgotpw.html')
    return HttpResponse(template.render())