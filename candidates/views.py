from django.http import HttpResponse
from django.template import loader

from candidates.models import Cand, User


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

def fruit(request):
    template = loader.get_template('fruit.html')
    context = {
        'fruits': ['Apple', 'Banana', 'Cherry'],   
    }
    return HttpResponse(template.render(context, request))