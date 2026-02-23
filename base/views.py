from django.shortcuts import render

from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect

from base.models import Candidate
from django.contrib.auth.models import User


def submit_application(request):
    template = loader.get_template('submit_application.html')
    return HttpResponse(template.render(request=request))


def application(request):
    template = loader.get_template('application.html')

    if request.method == 'POST':
        # Process the submitted application data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        linkedin_url = request.POST.get('linkedin_url', '').strip()
        bio = request.POST.get('bio', '').strip()
        # Add more fields as needed from your form

        # Create the Candidate (no User yet, unless you want to add login support)
        Candidate.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            linkedin_url=linkedin_url,
            bio=bio,
        )
        return redirect('/submit_application/')

    return HttpResponse(template.render(request=request))


def about(request):
    template = loader.get_template('about.html')
    return HttpResponse(template.render())


def candidates(request):
    mycandidates = Candidate.objects.all()
    template = loader.get_template('all_candidates.html')
    context = {
        'mycandidates': mycandidates
    }
    return HttpResponse(template.render(context, request))


def details(request, id):  #id comes from the URL
    mycandidate = Candidate.objects.get(id=id)
    template = loader.get_template('details.html')
    context = {
        'mycandidate': mycandidate,
    }
    return HttpResponse(template.render(context, request))


def main(request):
    template = loader.get_template('main.html')
    return HttpResponse(template.render())


def home(request):
    return render(request, "tailwinds/home.html", {})


def login(request):
    template = loader.get_template('auth/login.html')
    return HttpResponse(template.render(request=request))


def forgotpw(request):
    template = loader.get_template('auth/forgotpw.html')
    return HttpResponse(template.render(request=request))
