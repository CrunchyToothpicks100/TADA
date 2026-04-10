import random

from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from base.forms import CandidateForm, ContinueApplicationForm, QuestionBuilderForm, QuestionForm
from base.models import Answer, AnswerChoice, Candidate, Company, Position, Question, QuestionChoice, Submission
from base.user_context import user_context


def _current_candidate(request):
    if request.user.is_authenticated:
        return request.user.candidate_profiles.first()
    return None


def _generate_continue_code():
    return f"{random.randint(0, 999999):06d}"


def _candidate_from_email(email):
    return Candidate.objects.filter(email__iexact=email).order_by("-created_at").first()


def _upsert_candidate(form, request):
    candidate = _current_candidate(request) or Candidate()

    for field in form.Meta.fields:
        setattr(candidate, field, form.cleaned_data[field])

    candidate.save()
    return candidate


def _ensure_candidate_user(candidate):
    code = candidate.continue_code or _generate_continue_code()

    user = candidate.user
    if user is None:
        user = User(
            username=f"candidate-{candidate.external_id.hex[:12]}",
            email=candidate.email,
            first_name=candidate.first_name,
            last_name=candidate.last_name,
        )
    else:
        user.email = candidate.email
        user.first_name = candidate.first_name
        user.last_name = candidate.last_name

    user.set_password(code)
    user.save()

    candidate.user = user
    candidate.continue_code = code
    candidate.save(update_fields=["user", "continue_code", "email", "first_name", "last_name", "phone", "linkedin_url", "bio"])
    return user, code


def _submission_for(candidate, position):
    submission = (
        Submission.objects
        .filter(candidate=candidate, position=position)
        .exclude(status=Submission.STATUS_DISCARDED)
        .order_by("-created_at")
        .first()
    )
    if submission is None:
        submission = Submission.objects.create(candidate=candidate, position=position)
    return submission


def _questions_for(position, page):
    return list(
        Question.objects.filter(is_active=True, page=page, company__isnull=True, position__isnull=True)
        .union(
            Question.objects.filter(is_active=True, page=page, company=position.company, position__isnull=True),
            Question.objects.filter(is_active=True, page=page, position=position),
        )
        .order_by("sort_order", "id")
    )


def _answers_by_question(submission):
    answers = (
        submission.answers
        .select_related("choice", "question")
        .prefetch_related("multi_choices__choice")
    )
    return {answer.question_id: answer for answer in answers}


def _save_submission_payload(submission):
    submission.payload = {
        "candidate": {
            "first_name": submission.candidate.first_name,
            "last_name": submission.candidate.last_name,
            "email": submission.candidate.email,
            "phone": submission.candidate.phone,
            "linkedin_url": submission.candidate.linkedin_url,
            "bio": submission.candidate.bio,
        },
        "position_title": submission.position.title if submission.position_id else "",
    }


def _save_answers(form, submission, questions):
    for question in questions:
        answer, _ = Answer.objects.get_or_create(submission=submission, question=question)
        answer.int_value = None
        answer.bool_value = None
        answer.text_value = ""
        answer.choice = None
        answer.save()
        answer.multi_choices.all().delete()

        value = form.cleaned_data.get(form.field_name(question))
        if question.question_type == Question.TYPE_TEXT:
            answer.text_value = value or ""
        elif question.question_type == Question.TYPE_RATING:
            answer.int_value = value
        elif question.question_type == Question.TYPE_YESNO:
            answer.bool_value = value
        elif question.question_type == Question.TYPE_SINGLE:
            answer.choice = QuestionChoice.objects.filter(question=question, value=value).first()
        elif question.question_type == Question.TYPE_MULTI:
            for choice in question.choices.filter(value__in=value):
                AnswerChoice.objects.get_or_create(answer=answer, choice=choice)

        answer.save()


def _selected_company_for_user(request):
    user = request.user
    company_id = request.GET.get("company_id") or request.POST.get("company_id")

    if user.is_superuser:
        companies = list(Company.objects.filter(is_active=True).order_by("title"))
    else:
        companies = [membership.company for membership in user.company_staff.select_related("company").all()]

    selected_company = next((company for company in companies if str(company.id) == str(company_id)), None)
    if selected_company is None and companies:
        selected_company = companies[0]
    return selected_company


def _can_manage_company_questions(user, company):
    if user.is_superuser:
        return True
    if not company:
        return False
    return user.company_staff.filter(company=company, is_admin=True).exists()


def _scope_label(question):
    if question.position_id:
        return "Position-specific"
    if question.company_id:
        return "Company-wide"
    return "Global"


def _save_question_form(question, form, selected_company, position=None):
    if question is None:
        scope = form.cleaned_data["scope"]
        question_company = None
        question_position = None

        if scope == "company":
            question_company = selected_company
        elif scope == "position":
            question_company = selected_company
            question_position = position

        question = Question(
            company=question_company,
            position=question_position,
            question_type=form.cleaned_data["question_type"],
        )

    question.prompt = form.cleaned_data["prompt"].strip()
    question.help_text = form.cleaned_data["help_text"].strip()
    question.is_required = form.cleaned_data["is_required"]
    question.page = form.cleaned_data["page"]
    question.sort_order = form.cleaned_data["sort_order"]
    question.save()

    if question.question_type in {Question.TYPE_SINGLE, Question.TYPE_MULTI}:
        question.choices.all().delete()
        for choice in form.build_choices():
            QuestionChoice.objects.create(question=question, **choice)
    else:
        question.choices.all().delete()

    return question


def logout_view(request):
    logout(request)
    return redirect('/careers/')


def submit_application(request):
    context = {
        "continue_code": request.session.pop("application_continue_code", ""),
        "position_title": request.session.pop("application_position_title", ""),
    }
    return render(request, 'submit_application.html', context)


def application_continue(request):
    form = ContinueApplicationForm(request.POST or None)
    next_url = request.GET.get("next") or request.POST.get("next") or "/dashboard/"
    error_message = ""

    if request.method == "POST" and form.is_valid():
        candidate = (
            Candidate.objects
            .select_related("user")
            .filter(email__iexact=form.cleaned_data["email"], continue_code=form.cleaned_data["continue_code"], user__isnull=False)
            .order_by("-created_at")
            .first()
        )
        if candidate and candidate.user:
            auth_login(request, candidate.user)
            return redirect(next_url)
        error_message = "We could not find a matching application for that email and code."

    return render(
        request,
        "auth/continue_application.html",
        {
            "form": form,
            "next": next_url,
            "error_message": error_message,
        },
    )


def application(request, position_id, page):
    position = get_object_or_404(Position, id=position_id, is_active=True)
    page = int(page)

    if request.user.is_authenticated and (request.user.is_superuser or request.user.company_staff.exists()):
        return redirect(f"/dashboard/?company_id={position.company_id}")

    if page == 1:
        candidate = _current_candidate(request)
        form = CandidateForm(request.POST or None, instance=candidate)
        if request.method == "POST" and form.is_valid():
            existing_candidate = _candidate_from_email(form.cleaned_data["email"])
            if existing_candidate and (candidate is None or existing_candidate.id != candidate.id):
                form.add_error(
                    "email",
                    "An application already exists for this email. Use your 6-digit code to continue it.",
                )
                return render(
                    request,
                    "application.html",
                    {
                        "position": position,
                        "position_id": position_id,
                        "page": page,
                        "form": form,
                        "continue_code": candidate.continue_code if candidate else "",
                    },
                )

            candidate = _upsert_candidate(form, request)
            user, continue_code = _ensure_candidate_user(candidate)
            auth_login(request, user)

            submission = _submission_for(candidate, position)
            _save_submission_payload(submission)
            submission.save(update_fields=["payload"])

            request.session["application_continue_code"] = continue_code
            request.session["application_position_title"] = position.title
            return redirect("application", position_id=position.id, page=2)

        return render(
            request,
            "application.html",
            {
                "position": position,
                "position_id": position_id,
                "page": page,
                "form": form,
                "continue_code": candidate.continue_code if candidate else "",
            },
        )

    candidate = _current_candidate(request)
    if not candidate:
        return redirect(f"/application/continue/?next=/application/{position.id}/{page}/")

    submission = _submission_for(candidate, position)
    questions = _questions_for(position, page)
    form = QuestionForm(
        request.POST or None,
        questions=questions,
        answers_by_question_id=_answers_by_question(submission),
    )

    if request.method == "POST" and form.is_valid():
        _save_answers(form, submission, questions)
        _save_submission_payload(submission)
        submission.status = Submission.STATUS_FINISHED
        submission.finished_at = timezone.now()
        submission.edited_at = timezone.now()
        submission.save(update_fields=["payload", "status", "finished_at", "edited_at"])
        request.session["application_continue_code"] = candidate.continue_code
        request.session["application_position_title"] = position.title
        return redirect("/submit_application/")

    return render(
        request,
        "application.html",
        {
            "position": position,
            "position_id": position_id,
            "page": page,
            "form": form,
            "continue_code": candidate.continue_code,
        },
    )


def about(request):
    return render(request, "about.html")


@login_required
def details(request, id):
    if not request.user.is_superuser and not request.user.company_staff.exists():
        return HttpResponse("Unauthorized: Staff access required.")
    mycandidate = get_object_or_404(
        Candidate.objects.prefetch_related(
            "submissions__position__company",
            "submissions__answers__question",
            "submissions__answers__choice",
            "submissions__answers__multi_choices__choice",
        ),
        id=id,
    )
    context = {
        'mycandidate': mycandidate,
        'submissions': mycandidate.submissions.all().order_by("-created_at"),
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
def question_manager(request, position_id=None):
    position = None
    selected_company = None

    if position_id is not None:
        position = get_object_or_404(Position.objects.select_related("company"), id=position_id)
        selected_company = position.company
    else:
        selected_company = _selected_company_for_user(request)

    if not _can_manage_company_questions(request.user, selected_company):
        return HttpResponse("Unauthorized: You are not an admin for this company.")

    include_position_scope = position is not None
    form = QuestionBuilderForm(request.POST or None, include_position_scope=include_position_scope)

    if request.method == "POST" and form.is_valid():
        _save_question_form(None, form, selected_company, position=position)

        if position:
            return redirect("position_questions", position_id=position.id)
        return redirect(f"/dashboard/questions/?company_id={selected_company.id}")

    global_questions = Question.objects.filter(
        company__isnull=True,
        position__isnull=True,
    ).prefetch_related("choices").order_by("is_active", "page", "sort_order", "id")
    company_questions = Question.objects.filter(
        company=selected_company,
        position__isnull=True,
    ).prefetch_related("choices").order_by("is_active", "page", "sort_order", "id")
    position_questions = Question.objects.none()
    inherited_questions = []

    if position:
        position_questions = Question.objects.filter(position=position).prefetch_related("choices").order_by("is_active", "page", "sort_order", "id")
        inherited_questions = list(global_questions) + list(company_questions)

    summary_counts = {
        "global_active": sum(1 for question in global_questions if question.is_active),
        "company_active": sum(1 for question in company_questions if question.is_active),
        "position_active": sum(1 for question in position_questions if question.is_active) if position else 0,
    }

    return render(
        request,
        "staff/question_manager.html",
        {
            "position": position,
            "selected_company": selected_company,
            "form": form,
            "global_questions": global_questions,
            "company_questions": company_questions,
            "position_questions": position_questions,
            "inherited_questions": inherited_questions,
            "summary_counts": summary_counts,
        },
    )


@login_required
def edit_question(request, question_id):
    question = get_object_or_404(
        Question.objects.select_related("company", "position__company").prefetch_related("choices"),
        id=question_id,
    )
    selected_company = question.position.company if question.position_id else question.company or _selected_company_for_user(request)

    if not _can_manage_company_questions(request.user, selected_company):
        return HttpResponse("Unauthorized: You are not an admin for this company.")

    position = question.position if question.position_id else None
    form = QuestionBuilderForm(
        request.POST or None,
        include_position_scope=position is not None,
        question=question,
    )

    if request.method == "POST" and form.is_valid():
        _save_question_form(question, form, selected_company, position=position)
        if position:
            return redirect("position_questions", position_id=position.id)
        return redirect(f"/dashboard/questions/?company_id={selected_company.id}")

    return render(
        request,
        "staff/edit_question.html",
        {
            "question": question,
            "position": position,
            "selected_company": selected_company,
            "form": form,
            "scope_label": _scope_label(question),
        },
    )


@login_required
def archive_question(request, question_id):
    question = get_object_or_404(Question.objects.select_related("company", "position__company"), id=question_id)
    selected_company = question.position.company if question.position_id else question.company or _selected_company_for_user(request)

    if not _can_manage_company_questions(request.user, selected_company):
        return HttpResponse("Unauthorized: You are not an admin for this company.")

    if request.method != "POST":
        return HttpResponse("Method not allowed.")

    question.is_active = not question.is_active
    question.save(update_fields=["is_active"])

    if question.position_id:
        return redirect("position_questions", position_id=question.position_id)
    return redirect(f"/dashboard/questions/?company_id={selected_company.id}")


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
