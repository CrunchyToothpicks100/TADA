from django.shortcuts import render, get_object_or_404

from django.http import HttpResponse
from django.shortcuts import redirect

from base.models import Candidate
from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from base.user_context import user_context

def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/')


def submit_application(request):
    return render(request, 'submit_application.html')


def application(request, position_id, page):
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
        'position_id': position_id,
        'page': page,
    }

    return render(request, 'application.html', context)


def about(request):
    return render(request, "about.html")


def details(request, id):  #id comes from the URL
    mycandidate = Candidate.objects.get(id=id)
    context = {
        'mycandidate': mycandidate,
    }
    return render(request, 'staff/details.html', context)


def home(request):
    from base.models import Company, Position
    context = {
        'companies': Company.objects.filter(is_active=True),
        'positions': Position.objects.filter(is_active=True),
    }
    return render(request, "home.html", context) 


def login(request):
    from django.contrib.auth import authenticate, login as auth_login

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


@login_required
def dashboard(request):
    ctx = user_context(request)
    return render(request, 'dashboard.html', ctx)


@login_required
def add_position(request):
    from base.models import Position

    # Resolve which company to add the position to
    if not request.user.is_superuser:
        membership = request.user.company_staff.filter(is_admin=True).first()
        if not membership:
            return HttpResponse("Unauthorized: You are not an admin for any company.")
        company = membership.company
    else:
        from base.models import Company
        company_id = request.GET.get('company_id') or request.POST.get('company_id')
        company = get_object_or_404(Company, id=company_id) if company_id else None
        if not company:
            return HttpResponse("Please specify a company_id.")

    if request.method == 'POST':
        position = Position.objects.create(
            company=company,
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

@login_required
def delete_position(request, id):
    from base.models import Position
    position = get_object_or_404(Position, id=id)
    user = request.user

    # Only company admins for this position's company, or superusers, may delete
    if not user.is_superuser:
        return HttpResponse("Unauthorized: Only superusers can delete positions.")

    if request.method == 'POST':
        company_id = position.company_id
        position.delete()
        return redirect(f'/dashboard/?company_id={company_id}')