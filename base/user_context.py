from base.models import Company, Position, Candidate, Submission

# Warning: only call this from views that are strictly for staff/admin/super users
def user_context(request):
    user = request.user

    # Superusers see all active companies; staff see only their own
    if user.is_superuser:
        all_companies = list(Company.objects.filter(is_active=True))
        is_super = True
        is_admin = True
        is_staff = True
        candidates = Candidate.objects.all()
    elif user.company_staff.exists():
        all_companies = [m.company for m in user.company_staff.select_related('company').all()]
        is_super = False
        is_admin = None  # resolved after selected_company is known
        is_staff = True
        candidates = 0
    elif Candidate.objects.filter(user=request.user).exists():
        candidate = user.candidate_profiles.first()
        return {
            'is_super': False,
            'is_admin': False,
            'is_staff': False,
            'is_candidate': True,
            'my_applications': Submission.objects.filter(candidate=candidate),
        }

    # Determine selected company from ?company_id= query param, defaulting to the first
    company_id = request.GET.get('company_id')
    selected_company = next((c for c in all_companies if str(c.id) == company_id), None)
    if selected_company is None and all_companies:
        selected_company = all_companies[0]

    # Resolve per-company admin status for non-superusers
    if not user.is_superuser:
        membership = user.company_staff.filter(company=selected_company).first()
        is_admin = True if membership and membership.is_admin else False

    return {
        'all_companies': all_companies,
        'selected_company': selected_company,
        'is_super': is_super,
        'is_admin': is_admin,
        'is_staff': is_staff,
        'positions': Position.objects.filter(company=selected_company) if selected_company else [],
        'submissions': Submission.objects.filter(position__company=selected_company) if selected_company else [],
        'candidates': Candidate.objects.all(),   # May not be practical in the future for large Candidate datasets
        'my_applications': Submission.objects.filter(candidate=user.candidate_profiles.first()) if user.candidate_profiles.exists() else [],
        'is_candidate': Candidate.objects.filter(user=request.user).exists(),
    }
