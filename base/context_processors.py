from base.models import Company


def staff_context(request):
    user = request.user

    # Skip unauthenticated users (e.g. login page)
    if not user.is_authenticated:
        return {}

    # Superusers see all active companies; staff see only their own
    if user.is_superuser:
        all_companies = list(Company.objects.filter(is_active=True))
    elif user.company_staff.exists():
        all_companies = [m.company for m in user.company_staff.select_related('company').all()]
    else:
        # Authenticated but not staff or superuser (e.g. candidate) — nothing to inject
        return {}

    # Determine selected company from ?company_id= query param, defaulting to the first
    company_id = request.GET.get('company_id')
    selected_company = next((c for c in all_companies if str(c.id) == company_id), None)
    if selected_company is None and all_companies:
        selected_company = all_companies[0]

    # Superusers are always admin; otherwise check the CompanyStaff record
    if user.is_superuser:
        is_company_admin = True
    else:
        membership = user.company_staff.filter(company=selected_company).first()
        is_company_admin = membership.is_admin if membership else False

    return {
        'all_companies': all_companies,
        'selected_company': selected_company,
        'is_company_admin': is_company_admin,
    }
