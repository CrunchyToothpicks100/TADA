from django.shortcuts import render, get_object_or_404

from django.http import HttpResponse
from django.template import loader
from django.shortcuts import redirect

from base.models import Candidate
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from base.context import staff_context

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
    return render(request, 'staff/details.html', context)


def home(request):
    return render(request, "home.html", {})


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
            return HttpResponse("Invalid email or password. Does not exist.")

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            return HttpResponse("Invalid email or password. (Invalid credentials).")

    return render(request, 'auth/login.html')


def forgotpw(request):
    return render(request, 'auth/forgotpw.html')


# Candidate Dashboard View
@login_required
def candidate_dashboard(request):
    user = request.user
    candidate = getattr(user, 'candidate_profile', None)
    applications = []
    context = {
        'applications': applications,
        'candidate': candidate,
        'is_candidate': True,
    }
    return render(request, 'candidate_dashboard.html', context)


# Staff Dashboard View
@login_required
def staff_or_admin_dashboard(request):
    from base.models import Position, Submission

    ctx = staff_context(request)
    selected_company = ctx.get('selected_company')

    context = {
        **ctx,
        'positions': Position.objects.filter(company=selected_company) if selected_company else [],
        'applications': Submission.objects.filter(position__company=selected_company) if selected_company else [],
        'is_candidate': Candidate.objects.filter(user=request.user).exists(),
    }
    if ctx.get('is_admin'):
        return render(request, 'staff/admin_dashboard.html', context)
    else:
        return render(request, 'staff/staff_dashboard.html', context)

# Super Dashboard View
@login_required
def super_dashboard(request):
    from base.models import Position, Submission

    ctx = staff_context(request)
    selected_company = ctx.get('selected_company')

    context = {
        **ctx,
        'positions': Position.objects.filter(company=selected_company) if selected_company else [],
        'candidates': Candidate.objects.all(),
        'applications': Submission.objects.filter(position__company=selected_company) if selected_company else [],
        'is_candidate': Candidate.objects.filter(user=request.user).exists(),
    }
    return render(request, 'staff/super_dashboard.html', context)


@login_required
def dashboard(request):
    user = request.user
    
    if user.is_superuser:
        return super_dashboard(request)
    elif user.company_staff.exists():
        return staff_or_admin_dashboard(request)
    elif Candidate.objects.filter(user=request.user).exists():
        return candidate_dashboard(request)
    return HttpResponse("User type not recognized.")


@login_required
def edit_position(request, id):
    from base.models import Position
    position = get_object_or_404(Position, id=id)
    user = request.user

    # Only company admins for this position's company, or superusers, may edit
    if not user.is_superuser:
        membership = user.company_staff.filter(company=position.company, is_admin=True).first()
        if not membership:
            return HttpResponse("Unauthorized: You are not an admin for this company.")

    if request.method == 'POST':
        position.title = request.POST.get('title', '').strip()
        position.description = request.POST.get('description', '').strip()
        position.employment_type = request.POST.get('employment_type', position.employment_type)
        position.is_active = request.POST.get('is_active') == 'on'
        position.save()
        return redirect(f'/dashboard/?company_id={position.company_id}')

    context = {
        'position': position,
        'employment_type_choices': Position.EMPLOYMENT_TYPE_CHOICES,
    }
    return render(request, 'staff/edit_position.html', context)
