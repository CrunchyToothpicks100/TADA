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

There is no configured linter or formatter.

## Architecture

### Project layout

- `config/` — Django project settings and root URL conf
- `base/` — the single Django app; contains all models, views, urls, templates, and context processors

### URL routing

`config/urls.py` mounts everything under `/` via `base.urls`. All named URL patterns are in `base/urls.py`.

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

All models carry a `UUID external_id` for public-facing references (URLs should use this, not the integer PK).

### Roles and permissions

Enforced manually in views (no Django permission framework):

- **Superuser** (`is_superuser=True`) — sees all companies, always treated as admin
- **Company Admin** (`CompanyStaff.is_admin=True`) — can create/edit positions for their company
- **Company Staff** (`CompanyStaff.is_admin=False`) — read-only access to their company's data
- **Candidate** — has a `candidate_profile` reverse relation on `User`

### Context processor (`base/context_processors.py`)

`staff_context` runs on every request and injects three variables into all templates:

- `all_companies` — companies the user can access
- `selected_company` — resolved from `?company_id=` query param, defaulting to the first
- `is_company_admin` — whether the user is admin for the selected company

Views that need `selected_company` for DB queries should call `staff_context(request).get('selected_company')` rather than re-implementing the resolution logic.

### Templates

All templates extend `base/templates/master.html`. The `{% block style %}` block injects page-level CSS into the `<head>`.

### TODO features (not yet implemented)

See `TODO.md` for the full list. Key gaps:

- `create_job` view (create a new Position from the staff dashboard)
- `submission_detail` view (staff sets status; candidates edit answers)
- `staff_candidates` / `staff_candidate_details` views (the URL patterns are commented out in `base/urls.py`)
