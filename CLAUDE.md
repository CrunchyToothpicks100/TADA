# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is TADA

A Django-based hiring platform. Companies post positions, candidates apply via magic links, and staff manage submissions. The app has three user roles: superuser, company staff/admin, and candidate.

## Commands

All commands assume you are inside the Docker container (`docker exec -it tada-web-1 bash`). The container has a `pymg` alias for `python manage.py`.

```bash
# Start the app
docker compose up -d

# Shell into container
docker exec -it tada-web-1 bash

# Migrations
pymg makemigrations base
pymg migrate
pymg makemigrations --check   # detect unmade migrations

# Django system checks
pymg check

# Run tests
pymg test base

# Seed sample data
pymg create_cand    # creates 2 sample candidates
pymg create_staff   # creates a sample company with admin + staff users
```

There is no configured linter or formatter. Dependencies are managed with Poetry (see `pyproject.toml`).

Tests are not yet written — `base/tests.py` exists but is empty.

## Architecture

### Project layout

- `config/` — Django project settings and root URL conf
- `base/` — the single Django app; contains all models, views, urls, templates, and `context.py`

### URL routing

`config/urls.py` mounts everything under `/` via `base.urls`. All named URL patterns are in `base/urls.py`.

The single `/dashboard/` URL routes to the correct dashboard view based on user role (see `dashboard` view in `views.py`).

### Models (`base/models.py`)

Core entities and key design decisions:

| Model | Notes |
|---|---|
| `Company` | Org unit. Never deleted — only `is_active=False`. |
| `Position` | Job posting scoped to a company. Never deleted — only `is_active=False`. |
| `CompanyStaff` | Bridge table: User ↔ Company. `is_admin` is **per-company** — a user can be admin at one company and plain staff at another. |
| `Candidate` | Can be userless (pre-signup) or linked to a Django `User` via `OneToOneField`. |
| `ApplicationToken` | Magic-link token; expires in 3 days. On expiry, cascades to delete userless candidates. |
| `Submission` | A candidate's job application. Never deleted. Status workflow: `new → finished / discarded`. |
| `Question` | Scoped globally, per-company, or per-position via nullable FKs. Never deleted — only `is_active=False`. |
| `Answer` | Typed columns: `int_value`, `bool_value`, `text_value`, `choice` (FK to `QuestionChoice`). |
| `Note` | Staff notes on candidates; tracks `edited_at`. |

All models carry a `UUID external_id` for public-facing references (URLs should use this, not the integer PK). Note: current URL patterns still use `<int:id>` — this is a known design gap.

### Roles and permissions

Enforced manually in views (no Django permission framework). Failed checks return a plain `HttpResponse("Unauthorized: ...")` — not a redirect or error page.

- **Superuser** (`is_superuser=True`) — routed to `super_dashboard`, sees all companies, always treated as admin
- **Company Admin** (`CompanyStaff.is_admin=True`) — routed to `staff_or_admin_dashboard`, can create/edit positions
- **Company Staff** (`CompanyStaff.is_admin=False`) — routed to `staff_or_admin_dashboard`, read-only access
- **Candidate** — routed to `candidate_dashboard`

### Dashboard routing

All users hit `/dashboard/`. The `dashboard` view in `views.py` calls the appropriate view function directly (no redirect, URL stays `/dashboard/`):

```
/dashboard/ → super_dashboard(request)        # superusers
           → staff_or_admin_dashboard(request) # company staff/admin
           → candidate_dashboard(request)      # candidates
```

### `staff_context` (`base/context.py`)

`staff_context` is **not** registered as a Django context processor — it is called directly from views that need it. It returns `all_companies`, `selected_company` (resolved from `?company_id=` query param using the integer PK), `is_admin`, and `is_super`. Views merge it into their context dict with `**ctx`.

### Templates

All templates extend `base/templates/master.html`. The `{% block style %}` block injects page-level CSS into the `<head>`.

Reusable dashboard components live in `base/templates/dash-components/` and are included via `{% include %}`:

- `company_selector.html` — multi-company dropdown; always navigates to `/dashboard/?company_id=X`
- `job_postings.html` — positions list with edit button (admin only)
- `submissions.html` — applications list
- `candidates_list.html` — candidate links
- `my_applications.html` — candidate's own applications

### TODO features (not yet implemented)

See `TODO.md` for the full list. Key gaps:

- `create_job` view (create a new Position from the staff dashboard)
- `submission_detail` view (staff sets status; candidates edit answers)
- `staff_candidates` / `staff_candidate_details` views (URL patterns are commented out in `base/urls.py`)
