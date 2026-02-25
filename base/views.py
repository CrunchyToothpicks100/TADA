from django.shortcuts import render

from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect

from base.models import Candidate
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')


def submit_application(request):
    return render(request, 'submit_application.html')


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

    return render(request, 'application.html')


def about(request):
    return render(request, "about.html")


def candidates(request):
    mycandidates = Candidate.objects.all()
    context = {
        'mycandidates': mycandidates
    }
    return render(request, 'all_candidates.html', context)


def details(request, id):  #id comes from the URL
    mycandidate = Candidate.objects.get(id=id)
    context = {
        'mycandidate': mycandidate,
    }
    return render(request, 'details.html', context)


def home(request):
    return render(request, "home.html", {})


def home2(request):
    return render(request, "tailwinds/home2.html", {})


def login(request):
    from django.contrib.auth import authenticate, login as auth_login
    template = loader.get_template('auth/login.html')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # Find user by email
        from django.contrib.auth.models import User
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return HttpResponse("Invalid email or password. Does not exist. w")

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            auth_login(request, user)
            # Check Candidate or CompanyStaff
            from base.models import Candidate, CompanyStaff
            if hasattr(user, 'candidate_profile'):
                return redirect('/candidate_dashboard/')
            elif hasattr(user, 'company_staff'):
                return redirect('/staff_dashboard/')
            elif user.is_superuser:
                return redirect('/staff_dashboard/')
            else:
                return HttpResponse("User type not recognized.")
        else:
            return HttpResponse("Invalid email or password. (Invalid credentials).")

    return render(request, 'auth/login.html')


def forgotpw(request):
    return render(request, 'auth/forgotpw.html')


# Candidate Dashboard View
@login_required
def candidate_dashboard(request):
    user = request.user
    if (not hasattr(user, 'candidate_profile') 
        and not user.is_superuser):
        return HttpResponse("Unauthorized: You are not a candidate.")
    candidate = getattr(user, 'candidate_profile', None)
    # If you have an Application model, replace [] with a real query
    applications = []
    context = {
        'applications': applications,
        'candidate': candidate,
    }
    return render(request, 'candidate_dashboard.html', context)


# Staff Dashboard View
@login_required
def staff_dashboard(request):
    user = request.user
    if (not hasattr(user, 'company_staff') 
        and not user.is_superuser):
        return HttpResponse("Unauthorized: You are not a staff member.")
    staff = getattr(user, 'company_staff', None)
    jobs = []
    applications = []
    candidates = Candidate.objects.all()  # Example: get all candidates for display
    # -- to do -- 
    # jobs = Position.objects.filter(company=staff.company) if staff else []
    # applications = Application.objects.filter(job__company=staff.company) if staff else []
    from base.models import Position
    if staff:
        jobs = Position.objects.filter(company=staff.company)
    context = {
        'jobs': jobs,
        'applications': applications,
        'staff': staff,
        'candidates': candidates,
    }
    return render(request, 'staff_dashboard.html', context)
