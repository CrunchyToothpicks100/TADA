# User flow

### Quick definitions
    Non-Candidate -> No associated Candidate record
    Userless Candidate -> Candidate that has not finished their first application; Candidate.user is NULL
    User Candidate -> Candidate that has finished their first application; Candidate.user is set

### Security principle
    auth.User.email MUST be unique — the login-by-email flow depends on it.
    Enforce this at the database or validator level (Django does not enforce it by default).

    Candidate.email does NOT need a unique constraint. Transient duplicates are expected and
    self-clean when ApplicationTokens expire. Deduplication logic lives at the entry point (step 1).

    A password may never be set or changed on an existing account without first proving email
    ownership via a verification link sent to that address. Violating this is an account takeover.

---

## Application: Non-candidate

### Email does not match any existing auth.User

    -> Userless Candidate created
    -> ApplicationToken created (expiry details below)
    -> Token emailed as a magic link [EMAIL: magic_link]
    -> Submission is generated with candidate_id
    -> Answers are generated for every page submitted
    -> At form completion
        -> auth.User created with a random alphanumeric password
        -> Password emailed to candidate [EMAIL: initial_password]
        -> Form completion page has a login form that asks for the emailed password
        -> ApplicationToken deleted
    -> At first login
        -> Dashboard shows banner: "Set a personal password" (links to password change flow)

### Email matches a userless Candidate

    -> Create Candidate and token anyway
    -> Duplicate userless records self-delete on ApplicationToken expiry
    -> follow the usual flow

### Email matches an existing auth.User

    -> NO Userless Candidate created
    -> NO ApplicationToken created
    -> Submission is generated with the existing User Candidate with "needs_claim" set to True
    -> Candidate continues the form as normal
    -> At form completion
        -> The "Claim Application" email is sent
        -> They will see a different page that says "Good news! You already have an account 
                with us at (email address). We sent you an email to claim your application 
                for the (position) position

---

## Claiming a submission (needs_claim flow)

    The claim email contains a login link built with Django's PasswordResetTokenGenerator:

        /claim/<uidb64>/<token>/

    Security properties:
    -> One-time use: logging in changes last_login, which breaks the HMAC and invalidates the token
    -> Time-limited: respects PASSWORD_RESET_TIMEOUT (default 3 days, same as ApplicationToken)
    -> User-scoped: uidb64 encodes the User pk — cannot claim another user's submissions
    -> Unforgeable: HMAC signed with SECRET_KEY

    Claim view logic:
    1. Decode uidb64 -> get User
    2. Validate token with default_token_generator.check_token(user, token)
    3. If valid: log user in, set needs_claim=False on ALL their submissions, redirect to dashboard
    4. If invalid/expired: "This claim link has expired. Please log in directly."

    Normal login also triggers the sweep: on any successful login, set needs_claim=False
    on all Submission rows where submission.candidate.user = request.user.

    -> If the User has multiple unclaimed submissions, all are claimed in one login
    -> Unclaimed submissions (needs_claim=True) are hidden from the candidate dashboard
    -> Staff can see needs_claim submissions regardless

---

## Application: Logged-in User Candidate starts a new application

    -> Skip page 1 (they can update their info on their dashboard)
    -> Submission is generated with candidate_id
    -> Answers are generated for every page submitted

---

## Magic link flow

### ApplicationToken validated
    -> Session established
    -> ApplicationToken deleted
    -> Candidate fills out the rest of the form

### ApplicationToken invalid or expired
    -> "Sorry! Your link has expired."

---

## ApplicationToken rules

    -> Can only be used once
    -> Expires in 3 days
    -> On expiry: delete the token; if Candidate.user is NULL, delete the Candidate and cascade
       (CandidateAnswer, Submission, Answer, etc.)

---

## Candidate dashboard

    -> Change password (requires email verification) [EMAIL: password_change_verification]
    -> View submissions (needs_claim=False only)
    -> Edit answers in submissions (triggers Submission.edited_at)
    -> Edit bio / phone / email / linkedin_url
    -> Password tips shown on the password change page:
        - Use at least 8 characters
        - Do not reuse a password you have used with us before
        - Do not use dictionary words, your name, email, phone, or other guessable personal info
        - Do not reuse passwords across multiple online accounts

---

## User permissions

    Superuser:       is_superuser=True on auth.User
    Company admin:   CompanyStaff.is_admin=True for a given company
    Company staff:   CompanyStaff.is_admin=False for a given company
    Candidate:       has a Candidate record linked to their User

    A user can hold CompanyStaff rows at multiple companies (one row per company).
    is_admin is scoped per company — admin at one, staff at another is valid.

### Superusers
    Create a Company
    Create company admins and staff members
    Bypass everything via /admin/ or management commands
    See the candidate dashboard
    See all staff dashboards with a dropdown to select company
    Create global questions

### Company admins
    See the staff dashboard for their own company only
    Create non-admin staff members via the dashboard
    Create new positions and application forms
    Create company-wide questions
    Do everything that company staff can do

### Company staff
    Use the staff dashboard for their own company only:
        - Filter/sort candidates
        - Filter/sort intake submissions
        - Make notes on candidates
        - Set the status of a submission
    Apply for any position once
    Apply across many positions or companies

---

## CRUD rules

### Company
    CREATE: superuser only
    UPDATE: superuser only
    DELETE: superuser only (via /admin/ or management commands)

### CompanyStaff
    CREATE: superuser (admins + staff), company admin (non-admin staff only)
    UPDATE: superuser only
    DELETE: superuser only

### Position
    CREATE: company admin, superuser
    UPDATE: company admin, superuser
    DELETE: never deleted — only marked inactive (is_active=False)

### Question
    CREATE: global → superuser only; company-wide → company admin; position-specific → company admin
    UPDATE: same rules as CREATE
    DELETE: never deleted — only marked inactive (is_active=False)

### Candidate
    CREATE: on page 1 submission (email does not belong to an existing User)
    UPDATE (user): set to existing Django User when Userless Candidate finishes form
    DELETE: cascaded when ApplicationToken expires and Candidate.user is NULL

### Django User
    CREATE: when Userless Candidate finishes form and no User with that email exists
    DELETE: never deleted directly — only via account merge (duplicate is deleted, primary kept)

### ApplicationToken
    CREATE: on page 1 submission, ONLY when email does not match an existing User
    DELETE: on use (magic link clicked), on form completion, or on expiry
        Expiry deletion cascades to Candidate/Submission/Answer if Candidate.user is NULL

### Submission
    CREATE: on page 1 submission, linked to candidate_id
    UPDATE (status): staff, company admin, superuser
    UPDATE (status → finished): when Userless Candidate finishes the form
    UPDATE (finished_at): set when status is set to finished
    UPDATE (edited_at): set whenever a candidate edits answers post-submission
    UPDATE (needs_claim → True): when form is completed and email matches an existing User
    UPDATE (needs_claim → False): when that User logs in (claim sweep on all their submissions)
    DELETE: never — positions are never deleted, and Submission.position is PROTECTED

### Answer / AnswerChoice
    CREATE: generated for every page submitted
    UPDATE: candidate (from dashboard), also triggers Submission.edited_at
    DELETE: cascaded when Submission is deleted (only via Candidate cascade)

### Note (staff notes on a Candidate)
    CREATE: staff, company admin, superuser
    UPDATE (body + edited_at): author only
    DELETE: author, company admin, superuser; also cascaded when Candidate is deleted

---

## Email templates needed

| Template ID                    | Trigger                                                                 | Recipient        | Contents                                                                 |
|-------------------------------|-------------------------------------------------------------------------|------------------|--------------------------------------------------------------------------|
| `magic_link`                  | Page 1 submitted; email does NOT match an existing User                 | Applicant        | Link to resume/complete the application; expiry warning (3 days)         |
| `initial_password`            | Userless Candidate completes form; new User created                     | New User         | Random temporary password; prompt to set a personal password on login    |
| `password_change_verification`| Candidate requests password change from dashboard                       | Candidate        | Verification link to confirm identity before allowing password change     |
| `claim_application`           | Userless Candidate completes form; email matched existing User          | Existing User    | Stateless login link (/claim/<uidb64>/<token>/); auto-claims all pending submissions on login |
