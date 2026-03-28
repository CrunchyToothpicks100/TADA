# User flow

### Quick definitions
    Non-Candidate -> No associated Candidate record
    Userless Candidate -> Candidate that has not verified their email; Candidate.user is NULL
    User Candidate -> Candidate whose email has been verified; Candidate.user is set

### Security principle
    auth.User.email MUST be unique — the login-by-email flow depends on it.
    Enforce this at the database or validator level (Django does not enforce it by default).

    Candidate.email does NOT need a unique constraint. Transient duplicates are expected and
    self-clean when ApplicationTokens expire. Deduplication logic lives at the entry point (step 1).

    Passwords are never used. Authentication is exclusively via one-time email tokens.
    A login link may never be issued to an address that is not already verified as belonging
    to that account. Violating this is an account takeover.

---

## Application: Non-candidate (email does not match any existing Candidate or auth.User)

    -> Page 1 submitted
        -> Userless Candidate created from form data
        -> ApplicationToken created and stored in session (candidate context saved to session)
        -> Verification email sent with button-link containing ApplicationToken [EMAIL: account_verification]
        -> Redirect to page 2

    -> Page 2+ (before email verification):
        -> Italic banner at top: "We sent you an email for account verification.
           Verify your account to save your progress."
        -> Submission is created when the candidate completes page 2
        -> Answers are generated for every page submitted

    -> Email verification button clicked (at any point):
        -> ApplicationToken validated
        -> Redirect to set-password page (password + confirm password fields)
        -> On password submission:
            -> auth.User created from Candidate data with the chosen password
            -> Candidate.user set to new auth.User
            -> All ApplicationTokens for this Candidate deleted
            -> User logged in immediately
            -> Redirect to login_success page

    -> Application completed without clicking verification:
        -> Banner shown: "We sent you an email for account verification.
           Verify your email to see your application status."

---

## Application: Email matches a Userless Candidate (not yet a User)

    -> Create a new Candidate and ApplicationToken anyway
    -> Duplicate userless records self-delete on ApplicationToken expiry
    -> Follow the usual Non-candidate flow (verification email sent, etc.)

---

## Application: Email matches an existing auth.User

    -> Show message: "An account with this email already exists. Please log in."
    -> No Candidate or Submission created at this point
    -> After login, the logged-in User Candidate flow applies

---

## Application: Logged-in User Candidate starts a new application

    -> Skip page 1 (they can update their info on their dashboard)
    -> Submission is generated with candidate_id
    -> Answers are generated for every page submitted

---

## Magic link / verification flow

### ApplicationToken validated
    -> Redirect to set-password page (password + confirm password fields)
    -> On password submission:
        -> auth.User created from Candidate data with the chosen password
        -> Candidate.user set to new auth.User
        -> All ApplicationTokens for this Candidate deleted
        -> User logged in immediately
        -> Redirect to login_success page

### ApplicationToken invalid or expired
    -> "Sorry! Your verification link has expired."
    -> If Candidate.user is still NULL, Candidate and all cascades are deleted on expiry

---

## ApplicationToken rules

    -> Can only be used once
    -> Expires in 3 days
    -> On expiry: delete the token; if Candidate.user is NULL, delete the Candidate and cascade
       (Submission, Answer, AnswerChoice, etc.)

    ### Browser persistence
    -> On Candidate + ApplicationToken creation (page 1 submit), set a persistent cookie:
           name:     application_token
           value:    ApplicationToken.token (UUID)
           max_age:  259200 (3 days, matching token expiry)
           httponly: True
           samesite: Lax
    -> On any page load during the application, if the user has no active session,
       read the cookie and look up the ApplicationToken:
           -> Valid: restore candidate context and continue the form
           -> Invalid/expired/missing: treat as a fresh visitor
    -> Cookie is deleted when the token is deleted (verification clicked, form completed, or expiry)

---

## Login

    The login page asks for email and password.
    Passwords are set during email verification (set-password page after clicking the
    verification link). There is no separate registration page — account creation is
    always triggered by starting an application.

    Password tips shown on the set-password page and the password change page:
        - Use at least 8 characters
        - Do not reuse a password you have used with us before
        - Do not use dictionary words, your name, email, phone, or other guessable personal info
        - Do not reuse passwords across multiple online accounts

---

## login_success page

    Shown immediately after account creation (set-password form submitted) and after
    any successful login.

    Content:
    -> "You are now logged in!"
    -> Check for Submissions where status=new (not finished or discarded):
        -> For each: render a link — "Go back to (Position.title) application form"
        -> Link destination: the application form at the next page after the last
           completed page, determined by:
               max(Answer.question.page) across all Answers for that Submission + 1
           If no Answers exist yet, link to page 2 (page 1 is the candidate info form).
    -> If no uncompleted submissions: show a link to the candidate dashboard

---

## Candidate dashboard

    -> View submissions (own only)
    -> Edit answers in submissions (triggers Submission.edited_at)
    -> Edit bio / phone / email / linkedin_url
    -> Phone number verification (recommended)
        -> Candidate can verify their phone number via SMS OTP
        -> Shown with a "(recommended)" label in the dashboard

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
    CREATE: on page 1 submission (email does not match any existing auth.User)
    UPDATE (user): set to new Django User when email verification link is clicked
    DELETE: cascaded when ApplicationToken expires and Candidate.user is NULL

### Django User
    CREATE: when candidate submits the set-password form after clicking the verification link
    DELETE: never deleted directly — only via account merge (duplicate is deleted, primary kept)

### ApplicationToken
    CREATE: on page 1 submission, ONLY when email does not match an existing auth.User
    DELETE: on use (verification link clicked) or on expiry
        Expiry deletion cascades to Candidate/Submission/Answer if Candidate.user is NULL

### Submission
    CREATE: when the candidate completes page 2 (not page 1)
    UPDATE (status): staff, company admin, superuser
    UPDATE (status → finished): when candidate completes the full form
    UPDATE (finished_at): set when status is set to finished
    UPDATE (edited_at): set whenever a candidate edits answers post-submission
    DELETE: never — positions are never deleted, and Submission.position is PROTECTED

### Answer / AnswerChoice
    CREATE: generated for every page submitted (from page 2 onward)
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
| `account_verification`        | Page 1 submitted; email does NOT match an existing auth.User            | Applicant        | Button-link to verify account (ApplicationToken); expiry warning (3 days) |
| `password_change_verification`| Candidate requests password change from dashboard                       | Candidate        | Verification link to confirm identity before allowing password change     |
