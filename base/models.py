from django.db import models
import uuid


class Position(models.Model):
    """
    Job position within a company (e.g., Software Engineer, Sales Manager).
    Each company can have many positions.

    IMPORTANT: Positions are never deleted, only marked inactive, to preserve submission history.
    """
    EMPLOYMENT_FULL_TIME = "full_time"
    EMPLOYMENT_PART_TIME = "part_time"
    EMPLOYMENT_CONTRACT = "contract"
    EMPLOYMENT_INTERNSHIP = "internship"
    EMPLOYMENT_TEMPORARY = "temporary"
    EMPLOYMENT_TYPE_CHOICES = [
        (EMPLOYMENT_FULL_TIME, "Full-time"),
        (EMPLOYMENT_PART_TIME, "Part-time"),
        (EMPLOYMENT_CONTRACT, "Contract"),
        (EMPLOYMENT_INTERNSHIP, "Internship"),
        (EMPLOYMENT_TEMPORARY, "Temporary"),
    ]

    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name="positions")
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_positions"
    )
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default=EMPLOYMENT_FULL_TIME,
        db_index=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(employment_type__in=[
                    "full_time", "part_time", "contract", "internship", "temporary"
                ]),
                name="check_position_employment_type",
            ),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company.title}"


class Company(models.Model):
    """
    A company inside your greater org (espresso repair, 2A startup, vehicle ads, etc).
    Candidates can be recruited across companies, and staff can operate per-company.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_companies"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CompanyStaff(models.Model):
    """
    Bridge table linking a user to one or more companies as staff/admin.
    is_admin is per-company: a user can be admin at one company and staff at another.
    """
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="company_staff")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="staff")

    # admin vs staff, scoped per company
    is_admin = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "company"], name="uniq_companystaff_user_company"),
        ]

    def __str__(self):
        return f"{self.user} @ {self.company}"


class Candidate(models.Model):
    """
    Core person record.

    Lifecycle:
      Userless Candidate — user is NULL; created on page-1 submission before the
        form is completed. Deleted (with cascades) when its ApplicationToken expires.
      User Candidate — user is set when the candidate finishes their first application.
        Never deleted directly; only via account-merge cascade.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidate_profiles",
    )

    email = models.EmailField(db_index=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=40)    
    linkedin_url = models.URLField(blank=True)

    # freeform summary written by the candidate
    bio = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["last_name", "first_name"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__contains="@"),
                name="check_candidate_email",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class CandidateInterest(models.Model):
    """
    Lightweight "interest graph" that makes cross-company matching easy.
    Examples: cars, guns, coffee, python, sportscars, etc.
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="interests")
    label = models.CharField(max_length=120)  # e.g. "Cars", "Guns", "Python"
    strength_1_to_10 = models.PositiveSmallIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["candidate", "label"], name="uniq_candidate_interest_label"),
            models.CheckConstraint(
                condition=models.Q(strength_1_to_10__gte=1) & models.Q(strength_1_to_10__lte=10),
                name="check_interest_strength_1_to_10",
            ),
        ]

    def __str__(self):
        return f"{self.candidate} -> {self.label}"


class Note(models.Model):
    """
    Internal notes written by staff/admins about a candidate.
    CREATE: staff, company admin, superuser.
    UPDATE (body + edited_at): author only.
    DELETE: author, company admin, or superuser; cascades when Candidate is deleted.
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="authored_notes"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Note by {self.author} on {self.candidate}"


class Submission(models.Model):
    """
    Holds job application data for a candidate.
    Status transitions: new → finished (candidate completes form) or new → discarded (staff action).
    Never deleted — Submission.position is PROTECTED and positions are never deleted.
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Positions should not be deleted in practice
    # HOWEVER, position field is PROTECTED just in case
    position = models.ForeignKey(
        Position, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="submissions"
    )

    # A submission will always have a candidate (see notes.md) 
    candidate = models.ForeignKey(
        Candidate, 
        on_delete=models.CASCADE,
        related_name="submissions"
    )

    # snapshot of what they submitted
    payload = models.JSONField(default=dict, blank=True)

    # resolution workflow
    STATUS_NEW = "new"
    STATUS_DISCARDED = "discarded"
    STATUS_FINISHED = "finished"
    status = models.CharField(
        max_length=20,
        choices=[
            (STATUS_NEW, "New"),
            (STATUS_DISCARDED, "Discarded"),
            (STATUS_FINISHED, "Finished"),
        ],
        default=STATUS_NEW,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["new", "discarded", "finished"]),
                name="check_submission_status",
            ),
        ]

    def __str__(self):
        return f"{self.candidate} ({self.status})"


class Question(models.Model):
    """
    Custom questions attached to a scope level:

    Company   | Position  | Scope
    --------- | --------- | -----------------------------------------
    NULL      | NULL      | Global (all companies, all positions)
    Not null  | NULL      | Company-wide (all positions at a company)
    Not null  | Not null  | Position-specific

    IMPORTANT: Questions are never deleted, only marked inactive (is_active=False).
    """
    external_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Company deletions cascade to questions to prevent "global" orphans
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="questions",
    )

    # Position deletions cascade to questions to prevent "global" orphans
    position = models.ForeignKey(
        'Position',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='questions',
    )

    # question “shape”
    TYPE_RATING = "rating"      # usually 1-10
    TYPE_YESNO = "yesno"        # bool
    TYPE_TEXT = "text"          # free text
    TYPE_SINGLE = "single"      # single choice
    TYPE_MULTI = "multi"        # multi choice
    question_type = models.CharField(
        max_length=20,
        choices=[
            (TYPE_RATING, "Rating"),
            (TYPE_YESNO, "Yes/No"),
            (TYPE_TEXT, "Text"),
            (TYPE_SINGLE, "Single choice"),
            (TYPE_MULTI, "Multi choice"),
        ],
        default=TYPE_RATING,
        db_index=True,
    )

    prompt = models.TextField()

    help_text = models.CharField(max_length=240, blank=True)

    is_required = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    # page number in the application form; page 1 is reserved for candidate info + resume upload
    page = models.PositiveSmallIntegerField(default=2)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(question_type__in=[
                    "rating", "yesno", "text", "single", "multi"
                ]),
                name="check_question_type",
            ),
        ]

    def __str__(self):
        scope = "global"
        if (self.position_id):
            scope = self.position.title
        elif (self.company_id):
            scope = self.company.slug
        return f"[{scope}] {self.prompt[:60]}"


class QuestionChoice(models.Model):
    """
    Only used when question_type is single/multi.
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    label = models.CharField(max_length=140)
    value = models.SlugField(max_length=140)  # stable machine value
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["question", "value"], name="uniq_choice_value_per_question"),
            models.CheckConstraint(
                condition=models.Q(sort_order__gte=0),
                name="check_questionchoice_sort_order",
            ),
        ]

    def __str__(self):
        scope = "global"
        if (self.question.position_id):
            scope = self.question.position.title
        elif (self.question.company_id):
            scope = self.question.company.slug
        return f"{self.question} : {self.value}"


class Answer(models.Model):
    """
    One row per (submission, question).
    Stores different types in different columns.
    For multi-choice, we store selections in AnswerChoice.
    """
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")

    int_value = models.PositiveSmallIntegerField(null=True, blank=True)  # Question.TYPE_RATING
    bool_value = models.BooleanField(null=True, blank=True)              # Question.TYPE_YESNO
    text_value = models.TextField(blank=True)                            # Question.TYPE_TEXT

    # Question.TYPE_SINGLE
    choice = models.ForeignKey(
        QuestionChoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="selected_in_answers",
    )
    # Question.TYPE_MULTI — selections stored in AnswerChoice

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["submission", "question"], name="uniq_submission_question_answer"),
            models.CheckConstraint(
                condition=models.Q(int_value__isnull=True) | models.Q(int_value__gte=0),
                name="check_answer_int_value",
            ),
        ]
        indexes = [
            models.Index(fields=["question"]),
        ]

    def __str__(self):
        return f"{self.submission_id}:{self.question_id}"


class AnswerChoice(models.Model):
    """
    Multi-select bridge table.
    """
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="multi_choices")
    choice = models.ForeignKey(QuestionChoice, on_delete=models.CASCADE, related_name="multi_selected_in")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["answer", "choice"], name="uniq_answer_choice"),
        ]

    def __str__(self):
        return f"{self.answer_id}:{self.choice_id}"


class ApplicationToken(models.Model):
    """
    One-time magic link token for a candidate to resume or complete their application.
    Created when the candidate enters their email at the start of the application.
    Can only be used once. Expires after 3 days.
    On expiry: token is deleted; if Candidate.user is NULL, the Candidate (and all
    cascades: Submission, Answer, etc.) is also deleted.
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="application_tokens")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Token for {self.candidate} (used: {self.used_at is not None})"