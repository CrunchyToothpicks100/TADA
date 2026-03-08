# User flow

### Quick definitions
    Non-Candidate -> No associated Candidate
    Userless Candidate -> Candidate that has not finished their first application, user set to null
    User Candidate -> Candidate that has finished their first application, user associated

## Non-Candidate finishes page 1 of application (email, first_name, last_name, etc.)

### Email does not exist
    -> Userless Candidate created
    -> ApplicationToken created (expiry details below)
    -> Token emailed as a magic link
    -> Submission is generated with candidate_id
    -> Answers are generated for every page submitted

    (Add this to Non-login application page: "Lost your progress? Check email for magic link!")

    -> Create new Candidate and token anyways
    -> Any duplicate records get deleted on token expiry, no worries
    -> Candidate continues form

### User Candidate email exists
    -> Do NOT create a new Candidate or send a magic link
    -> Show: "An account with this email already exists. Please log in to continue."
    -> This prevents spurious magic link emails and stops attackers from spamming a victim's inbox
    -> Security note: attacker can't proceed without access to the victim's email anyway (magic link
       goes to the real owner), but we still block this path to avoid nuisance emails

## Userless Candidate finishes form
    Does a Django User with that email already exist?
    No:
        -> Django User created with random alphanumeric password
        -> Password emailed to candidate
        -> First dashboard login shows banner: "Set a personal password"
        -> ApplicationToken deleted
    Yes:
        -> Associate the new Candidate with the existing Django User (do NOT create a second User)
        -> Do NOT email a password (they already have one)
        -> ApplicationToken deleted

## Logged-in User Candidate works on a new application
    -> Skip page 1 (they can update their info on their dashboard)
    -> Submission is generated with candidate_id
    -> Answers are generated for every page submitted

## Candidate clicks magic link

### ApplicationToken validated
    -> session established
    -> ApplicationToken deleted
    -> Candidate fills out the rest of the form
### ApplicationToken invalid
    -> "Sorry! Your token expired."

## ApplicationToken:
    -> ApplicationToken CAN ONLY BE USED ONCE
    -> ApplicationToken expires in 3 days
    -> when ApplicationToken expires, delete it
    -> If the associated Candidate has a NULL User, delete the candidate and cascade the deletion to CandidateAnswer, Submission, etc.

## Account merging (edge case):
    -> If a User somehow ends up with duplicate accounts (same email), show a dashboard banner on login:
      "Looks like you have duplicate accounts. Would you like to merge them?"
    -> On confirmation: reassign all Candidates to the primary User, delete the duplicate User
    -> Only show this banner when logging in via password (magic link already resolves to a specific Candidate)

## Candidate dashboard:
    -> option to change password (verify through email)
    -> secure password tips! (add to webpage)
        -> use at least 8 characters
        -> Do not use the same password you have used with us previously
        -> Do not use dictionary words, your name, e-mail address, mobile phone number or other personal information that can be easily obtained.
        -> Do not use the same password for multiple online accounts.
    -> View submissions
    -> Edit answers in those submissions
    -> Edit bio/phone/email/linkedin_url

## User permissions rules
    A Django superuser has (is_superuser=True) in User
    A Company admin has (is_admin=True) in CompanyStaff for a given company
    A Company staff member has (is_admin=False) in CompanyStaff for a given company
    A user can be staff/admin at multiple companies (one CompanyStaff row per company)
    is_admin is scoped per company: a user can be admin at one and staff at another
    A Candidate has their own record in Candidate

### Superusers 
    Create a Company 
    Create company admins and staff members 
    Bypass everything with /admin/ or management commands 
    See the candidate dashboard 
    See all staff dashboards with a dropdown menu for selecting the company 
    Create global questions 

### Company admins 
    See the staff dashboard for their own company only 
    Create non-admin staff members using the dashboard 
    Create new job positions and application forms 
    Create company-wide questions 
    Do anything that the company staff can do 

### Company staff 
    Use the staff dashboard for their own company only 
    Only use the staff dashboard for 
        - Filtering/sorting candidates 
        - Filtering/sorting intake submissions 
        - Making notes on candidates 
        - Setting the status of an intake submission 
    Apply for any position once 
    Apply for many positions or companies

## CRUD notes

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
    CREATE: global questions → superuser only; company-wide → company admin; position-specific → company admin
    UPDATE: same rules as CREATE
    DELETE: never deleted — only marked inactive (is_active=False)

### Candidate
    CREATE: on page 1 submission (email does not belong to a User Candidate)
    UPDATE (user): set to existing Django User when Userless Candidate finishes form
    DELETE: cascaded when ApplicationToken expires and Candidate.user is NULL

### Django User
    CREATE: when Userless Candidate finishes form and no User with that email exists
    (never deleted directly — only via account merge, where the duplicate is deleted)

### ApplicationToken
    CREATE: on page 1 submission
    DELETE: on use (magic link clicked), on form completion, or on expiry
        expiry deletion also cascades to Candidate/Submission/Answer if Candidate.user is NULL

### Submission
    CREATE: on page 1 submission, linked to candidate_id
    UPDATE (status): staff, company admin, superuser (e.g. discard a submission)
    UPDATE (status → finished): when Userless Candidate finishes the form
    UPDATE (finished_at): set at the same time status is set to finished
    UPDATE (edited_at): set whenever a candidate edits answers post-submission
    (never deleted — positions are never deleted either, and Submission.position is PROTECTED)

### Answer / AnswerChoice
    CREATE: generated for every page submitted
    UPDATE: candidate (from dashboard), also triggers Submission.edited_at
    DELETE: cascaded when Submission is deleted (which only happens via Candidate cascade)

### Note (staff notes on a Candidate)
    CREATE: staff, company admin, superuser
    UPDATE (body + edited_at): author only
    DELETE: author, company admin, superuser; also cascaded when Candidate is deleted
