# TODO — Unimplemented URLs

## 1. `create_job` — Create Position
**URL:** `staff_dashboard/positions/create/`
**View:** `create_job`
**Who:** Company admin, superuser
**Notes:** Mirrors `edit_position` but creates a new `Position` linked to the selected company.
Referenced in: `staff_dashboard.html` "New Position" button (commented out).

---

## 2. `application_detail` — Submission Detail
**URL:** `staff_dashboard/submissions/<int:id>/` (staff) or a shared route
**View:** `application_detail`
**Who:** Staff/admin can set status (new → finished/discarded); candidates can view and edit their answers
**Notes:** Per notes.md — staff sets status, candidates edit answers (triggers `Submission.edited_at`).
Referenced in: `staff_dashboard.html` and `candidate_dashboard.html` (both commented out).

---

## 3. `staff_candidates` — Staff Candidate List
**URL:** `staff_dashboard/candidates/`
**View:** `staff_candidates`
**Who:** All staff, company admin, superuser
**Notes:** Filtered/sortable list of candidates. Already registered in urls.py (view not yet defined).

---

## 4. `staff_candidate_details` — Staff Candidate Detail + Notes
**URL:** `staff_dashboard/candidates/<int:id>/`
**View:** `staff_candidate_details`
**Who:** All staff, company admin, superuser
**Notes:** Single candidate view. Staff can create notes; authors can edit/delete their own notes;
company admins and superusers can delete any note. Already registered in urls.py (view not yet defined).
