from django.shortcuts import render, get_object_or_404

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
            return HttpResponse("Invalid email or password. Does not exist.")

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            auth_login(request, user)
            from base.models import Candidate, CompanyStaff
            if hasattr(user, 'candidate_profile'):
                return redirect('/candidate_dashboard/')
            elif user.is_superuser or user.company_staff.exists():
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
    from base.models import Position, CompanyStaff
    user = request.user

    staff_memberships = user.company_staff.select_related('company').all()
    if not user.is_superuser and not staff_memberships.exists():
        return HttpResponse("Unauthorized: You are not a staff member.")

    # Determine selected company from GET param, defaulting to first membership
    from base.models import Company
    if user.is_superuser:
        all_companies = Company.objects.filter(is_active=True)
    else:
        all_companies = [m.company for m in staff_memberships]

    selected_company = None
    company_id = request.GET.get('company_id')
    if company_id:
        selected_company = next((c for c in all_companies if str(c.id) == company_id), None)
    if selected_company is None and all_companies:
        selected_company = all_companies[0]

    if user.is_superuser:
        is_company_admin = True
    else:
        membership = staff_memberships.filter(company=selected_company).first()
        is_company_admin = membership.is_admin if membership else False

    positions = Position.objects.filter(company=selected_company) if selected_company else []
    candidates = Candidate.objects.all()
    applications = []

    context = {
        'all_companies': all_companies,
        'selected_company': selected_company,
        'is_company_admin': is_company_admin,
        'positions': positions,
        'applications': applications,
        'candidates': candidates,
    }
    return render(request, 'staff_dashboard.html', context)


@login_required
def edit_position(request, id):
    from base.models import Position, CompanyStaff
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
        return redirect(f'/staff_dashboard/?company_id={position.company_id}')

    context = {
        'position': position,
        'employment_type_choices': Position.EMPLOYMENT_TYPE_CHOICES,
    }
    return render(request, 'edit_position.html', context)
