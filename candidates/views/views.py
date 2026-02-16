from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect

from candidates.models import Cand, User


def submit_application(request):
    template = loader.get_template('submit_application.html')
    return HttpResponse(template.render(request=request))
    

def application(request):
    template = loader.get_template('application.html')
    
    if request.method == 'POST':
        # Process the submitted application data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        linkedin_url = request.POST.get('linkedin_url')
        resume_url = request.POST.get('resume_url')

        # Create a new User and Cand
        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        Cand.objects.create(
            user=user,
            linkedin_url=linkedin_url,
            resume_url=resume_url,
        )
        return redirect('/submit_application/')
    
    return HttpResponse(template.render(request=request))


def about(request):
    template = loader.get_template('about.html')
    return HttpResponse(template.render())


def candidates(request):
    mycandidates = Cand.objects.all()
    template = loader.get_template('all_candidates.html')
    context = {
        'mycandidates': mycandidates
    }
    return HttpResponse(template.render(context, request))


def details(request, id):  #id comes from the URL
    mycandidate = Cand.objects.get(id=id)
    template = loader.get_template('details.html')
    context = {
        'mycandidate': mycandidate,
    }
    return HttpResponse(template.render(context, request))


def main(request):
    template = loader.get_template('main.html')
    return HttpResponse(template.render())