from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

#import for forms.py
from base.forms import CandidateForm

from base.models import Candidate, Company, Position, Submission
from base.user_context import user_context


def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/careers/')


def submit_application(request):
    return render(request, 'submit_application.html')

# New application view for handling applications with the new forms.py ...
def application(request, position_id, page):
    position = get_object_or_404(Position, id=position_id, is_active=True)

    form = CandidateForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('/submit_application/')

    context = {
        'position': position,
        'position_id': position_id,
        'page': page,
        'form': form,
    }

    return render(request, 'application.html', context)

'''
def application(request, position_id, page):
    position = get_object_or_404(Position, id=position_id, is_active=True)

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

    context = {
        'position': position,
        'position_id': position_id,
        'page': page,
    }

    return render(request, 'application.html', context)
'''

def about(request):
    return render(request, "about.html")

@login_required
def details(request, id):
    if not request.user.is_superuser and not request.user.company_staff.exists():
        return HttpResponse("Unauthorized: Staff access required.")
    mycandidate = get_object_or_404(Candidate, id=id)
    context = {
        'mycandidate': mycandidate,
    }
    return render(request, 'staff/details.html', context)


def home(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    else:
        return redirect('/careers/')


def careers(request):
    context = {
        'companies': Company.objects.filter(is_active=True),
        'positions': Position.objects.filter(is_active=True),
    }
    return render(request, "careers.html", context)


def login(request):
    from django.contrib.auth import authenticate, login as auth_login

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return HttpResponse("Invalid email or password.")
        except User.MultipleObjectsReturned:
            return HttpResponse("Invalid email or password.")

        user = authenticate(request, username=user_obj.username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('/dashboard/')
        else:
            return HttpResponse("Invalid email or password.")

    return render(request, 'auth/login.html')


def forgotpw(request):
    return render(request, 'auth/forgotpw.html')


@login_required
def dashboard(request):
    ctx = user_context(request)
    return render(request, 'dashboard.html', ctx)


@login_required
def add_position(request):
    # Resolve which company to add the position to
    if not request.user.is_superuser:
        membership = request.user.company_staff.filter(is_admin=True).first()
        if not membership:
            return HttpResponse("Unauthorized: You are not an admin for any company.")
        company = membership.company
    else:
        company_id = request.GET.get('company_id') or request.POST.get('company_id')
        company = get_object_or_404(Company, id=company_id) if company_id else None
        if not company:
            return HttpResponse("Please specify a company_id.")

    if request.method == 'POST':
        position = Position.objects.create(
            company=company,
            created_by=request.user,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', '').strip(),
            employment_type=request.POST.get('employment_type', 'full_time'),
            is_active=request.POST.get('is_active') == 'on',
        )
        return redirect(f'/dashboard/?company_id={position.company_id}')

    context = {
        'company': company,
        'employment_type_choices': Position.EMPLOYMENT_TYPE_CHOICES,
    }
    return render(request, 'staff/add_position.html', context)


@login_required
def edit_position(request, id):
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


@login_required
def submission_detail(request, id):
    submission = get_object_or_404(
        Submission.objects.select_related('candidate', 'position__company')
                          .prefetch_related('answers__question', 'answers__choice', 'answers__multi_choices__choice'),
        id=id,
    )
    user = request.user
    is_candidate_owner = (
        hasattr(user, 'candidate_profiles') and
        user.candidate_profiles.filter(id=submission.candidate_id).exists()
    )
    is_staff_for_company = (
        user.is_superuser or
        (submission.position and user.company_staff.filter(company=submission.position.company).exists())
    )
    if not is_candidate_owner and not is_staff_for_company:
        return HttpResponse("Unauthorized: You do not have access to this submission.")

    is_admin = (
        user.is_superuser or
        (submission.position and user.company_staff.filter(company=submission.position.company, is_admin=True).exists())
    )

    if request.method == 'POST' and is_staff_for_company:
        new_status = request.POST.get('status')
        if new_status in (Submission.STATUS_NEW, Submission.STATUS_FINISHED, Submission.STATUS_DISCARDED):
            submission.status = new_status
            submission.save()
            return redirect('submission_detail', id=id)

    context = {
        'submission': submission,
        'answers': submission.answers.all(),
        'is_admin': is_admin,
        'is_staff': is_staff_for_company,
        'is_candidate_owner': is_candidate_owner,
    }
    return render(request, 'staff/submission_detail.html', context)
